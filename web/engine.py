from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from pdf_tool import (
    add_watermark,
    compress_pdf,
    convert_pdf_to_excel,
    convert_pdf_to_images,
    convert_pdf_to_text,
    convert_pdf_to_word,
    decrypt_pdf,
    delete_pages,
    encrypt_pdf,
    merge_pdfs,
    rotate_pdf,
    split_pdf,
)
from pdf_tool.pdf_to_text import ConversionStopped, pdf_page_count

DATA_DIR = Path(__file__).resolve().parent / "data"
RETENTION = timedelta(days=1)
PREVIEW_DPI = 120
PREVIEW_ACTIONS = {
    "rotate": "旋转",
    "watermark": "水印",
    "delete": "删除",
    "text": "提取文字",
}

QUEUED = "queued"
RUNNING = "running"
PENDING = "pending"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
STOPPED = "stopped"

TERMINAL = {COMPLETED, FAILED, CANCELLED, STOPPED}
TOOLS = (
    "to_text",
    "to_image",
    "split",
    "merge",
    "delete",
    "compress",
    "to_word",
    "to_excel",
    "rotate",
    "watermark",
    "encrypt",
    "decrypt",
)
PAGE_RANGE_TOOLS = (
    "to_text",
    "to_image",
    "split",
    "delete",
    "compress",
    "to_word",
    "to_excel",
    "rotate",
    "watermark",
)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex


def _stem(name: str) -> str:
    stem = Path(os.path.basename(name)).stem.strip()
    stem = re.sub(r'[<>:"/\\|?*]', "_", stem).strip(" .")
    return stem or "document"


def _is_pdf_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return b"%PDF" in handle.read(1024)
    except OSError:
        return False


def _parse_page_value(value, label: str):
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label}须是从 1 开始的正整数")
    return value


def _parse_page_list(value) -> list[int]:
    if value is None or value == "" or value == []:
        return []
    if isinstance(value, list):
        raw = ",".join(str(item) for item in value)
        if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
            raise ValueError("页码须是从 1 开始的正整数")
    elif isinstance(value, str):
        raw = value
    else:
        raise ValueError("页码须是从 1 开始的正整数")

    raw = raw.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
    if not raw.strip():
        return []

    pages = []
    seen = set()
    for part in re.split(r"[\s,]+", raw.strip()):
        if not part:
            continue
        if "-" in part or "—" in part or "－" in part:
            raise ValueError("请列举页码，例如 1, 4, 5")
        if not part.isdigit() or int(part) < 1:
            raise ValueError("页码须是从 1 开始的正整数")
        page = int(part)
        if page not in seen:
            seen.add(page)
            pages.append(page)
    return pages


def _parse_positive(value, default: int, label: str) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(label)
    return value


def _parse_non_negative(value, default: int, label: str) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(label)
    return value


def _parse_bool(value, default: bool) -> bool:
    if value is None or value == "":
        return default
    if not isinstance(value, bool):
        raise ValueError("参数不正确")
    return value


def normalize_params(tool: str, params) -> dict:
    if not isinstance(params, dict):
        raise ValueError("参数不正确")

    start = _parse_page_value(params.get("page_start"), "起始页")
    end = _parse_page_value(params.get("page_end"), "结束页")
    if tool in PAGE_RANGE_TOOLS and start is not None and end is not None and start > end:
        raise ValueError("起始页不能大于结束页")

    normalized = {
        "page_start": start,
        "page_end": end,
        "skip_pages": _parse_page_list(params.get("skip_pages")) if tool == "to_text" else [],
        "min_text_length": _parse_non_negative(
            params.get("min_text_length"), 50, "最短文字长度须是大于等于 0 的整数"
        ),
        "image_format": "png",
        "dpi": _parse_positive(params.get("dpi"), 200, "清晰度须是正整数"),
        "pages_per_file": _parse_positive(params.get("pages_per_file"), 1, "每份页数须是正整数"),
        "delete_pages": _parse_page_list(params.get("delete_pages")) if tool == "delete" else [],
        "compression_level": _parse_positive(
            params.get("compression_level"), 3, "压缩级别须在 1 到 5 之间"
        ),
        "include_images": _parse_bool(params.get("include_images"), True),
        "table_only": _parse_bool(params.get("table_only"), False),
        "angle": 90,
        "watermark_text": "",
        "password": "",
    }

    if tool == "to_image":
        image_format = params.get("image_format") or "png"
        if not isinstance(image_format, str):
            raise ValueError("图片格式只接受 png 或 jpg")
        image_format = image_format.lower()
        if image_format == "jpeg":
            image_format = "jpg"
        if image_format not in ("png", "jpg"):
            raise ValueError("图片格式只接受 png 或 jpg")
        normalized["image_format"] = image_format

    if tool == "compress":
        level = normalized["compression_level"]
        if params.get("compression_level") in (None, ""):
            level = 3
        if level < 1 or level > 5:
            raise ValueError("压缩级别须在 1 到 5 之间")
        normalized["compression_level"] = level

    if tool == "delete" and not normalized["delete_pages"]:
        raise ValueError("请填写要删除的页码")

    if tool == "rotate":
        angle = params.get("angle")
        if isinstance(angle, str) and angle.isdigit():
            angle = int(angle)
        if angle not in (90, 180, 270):
            raise ValueError("角度只接受 90、180 或 270")
        normalized["angle"] = angle

    if tool == "watermark":
        text = params.get("watermark_text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("请填写水印文字")
        text = text.strip()
        if len(text) > 80:
            raise ValueError("水印文字不能超过 80 个字")
        normalized["watermark_text"] = text

    if tool in ("encrypt", "decrypt"):
        password = params.get("password")
        if not isinstance(password, str) or not password.strip():
            raise ValueError("请填写口令")
        if len(password) > 128:
            raise ValueError("口令过长")
        normalized["password"] = password

    return normalized


def _pdf_page_count(path: Path) -> int:
    import fitz

    doc = fitz.open(path)
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ValueError("这份 PDF 已经加密，先解密再预览")
        if doc.page_count < 1:
            raise ValueError("这份 PDF 没有页面")
        return doc.page_count
    finally:
        doc.close()


def _shown_time(task: dict) -> datetime | None:
    raw = task.get("finished_at") or task.get("created_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _past_retention(task: dict, now: datetime) -> bool:
    if task.get("status") not in TERMINAL:
        return False
    moment = _shown_time(task)
    if moment is None:
        return False
    return now - moment > RETENTION


def _forget_password(task: dict) -> None:
    params = task.get("params")
    if isinstance(params, dict) and params.get("password"):
        params["password"] = ""


def _resolve_range(page_count: int, start: int | None, end: int | None) -> tuple[int, int]:
    if start is None:
        start = 1
    if end is None:
        end = page_count
    if start > page_count:
        raise ValueError(f"起始页 {start} 超出范围（PDF共 {page_count} 页）")
    end = min(end, page_count)
    if start > end:
        raise ValueError("没有可处理的页面")
    return start, end


def _text_skip_indexes(page_count: int, start: int | None, end: int | None, skip_pages: list[int]) -> list[int]:
    first, last = _resolve_range(page_count, start, end)
    chosen = set(range(first, last + 1))
    for page in skip_pages:
        chosen.discard(page)
    if not chosen:
        raise ValueError("没有可处理的页面")
    return [index for index in range(page_count) if index + 1 not in chosen]


def _blank_item(item_id: str, name: str) -> dict:
    return {
        "id": item_id,
        "name": name,
        "status": PENDING,
        "error": "",
        "page": 0,
        "page_count": 0,
        "page_errors": [],
        "output": "",
        "download_name": "",
        "preview": False,
        "images": [],
        "ratio": None,
    }


def _public_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "status": item["status"],
        "error": item["error"],
        "page": item["page"],
        "page_count": item["page_count"],
        "page_errors": item["page_errors"],
        "download": item["status"] == COMPLETED and bool(item["output"]),
        "preview": item["status"] == COMPLETED and item["preview"],
        "image_count": len(item.get("images") or []),
        "download_name": item["download_name"],
        "ratio": item["ratio"],
    }


def _public_task(task: dict) -> dict:
    return {
        "id": task["id"],
        "tool": task["tool"],
        "status": task["status"],
        "stop_requested": task["stop_requested"],
        "created_at": task["created_at"],
        "finished_at": task["finished_at"],
        "error": task["error"],
        "inputs": [{"name": item["name"]} for item in task["inputs"]],
        "items": [_public_item(item) for item in task["items"]],
        "preview_id": task.get("preview_id") or "",
        "action": task.get("action") or "",
        "page": task.get("page") or 0,
    }


def _public_preview(preview: dict) -> dict:
    return {
        "id": preview["id"],
        "name": preview["name"],
        "page_count": preview["page_count"],
        "revision": preview["revision"],
        "status": preview["status"],
        "error": preview.get("error") or "",
        "action": preview.get("action") or "",
        "action_page": preview.get("action_page") or 0,
        "last_action": preview.get("last_action") or "",
        "last_page": preview.get("last_page") or 0,
        "text": preview.get("text") or "",
        "text_page": preview.get("text_page") or 0,
        "created_at": preview["created_at"],
        "updated_at": preview.get("updated_at") or preview["created_at"],
    }


def _page_text(pdf_path: str, page_number: int) -> str:
    import fitz
    from pdf_tool.pdf_to_office import _is_scan_page, _ocr_lines
    from pdf_tool.pdf_to_text import recognize_pdf_page
    from pdf_tool.wechat_ocr import WeChatOCR

    doc = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"页码 {page_number} 超出范围（PDF共 {doc.page_count} 页）")
        page = doc[page_number - 1]
        scanned = _is_scan_page(page)
        if not scanned:
            return page.get_text("text").strip()
    finally:
        doc.close()

    ocr = WeChatOCR()
    image_dir = tempfile.mkdtemp(prefix="pdf-preview-")
    try:
        boxes, width = recognize_pdf_page(pdf_path, page_number, ocr, image_dir)
    finally:
        ocr.stop()
        shutil.rmtree(image_dir, ignore_errors=True)
    return "\n".join(_ocr_lines(boxes, width)).strip()


class Workbench:
    def __init__(self, root: Path | None = None):
        self.root = root or DATA_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "tasks.json"
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._closing = False
        self._tasks = []
        self._previews = []
        self._expired_at = datetime.min
        self._preview_path = self.root / "previews.json"
        self._load()
        self._load_previews()
        self._recover()
        self._expire()
        self._thread = threading.Thread(target=self._loop, name="workbench", daemon=True)
        self._thread.start()

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [_public_task(task) for task in reversed(self._tasks)]

    def preview_snapshot(self) -> list[dict]:
        with self._lock:
            return [_public_preview(preview) for preview in reversed(self._previews)]

    def open_preview(self, name: str, path: Path) -> dict:
        if not name.lower().endswith(".pdf") or not _is_pdf_file(path):
            raise ValueError(f"只接受 PDF 文件：{os.path.basename(name)}")
        page_count = _pdf_page_count(path)
        preview_id = _new_id()
        directory = self.root / "previews" / preview_id
        directory.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(path), str(directory / "source.pdf"))
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        now = _now()
        preview = {
            "id": preview_id,
            "name": os.path.basename(name),
            "page_count": page_count,
            "revision": 1,
            "status": "ready",
            "error": "",
            "action": "",
            "action_page": 0,
            "last_action": "",
            "last_page": 0,
            "text": "",
            "text_page": 0,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            self._previews.append(preview)
            self._save_previews()
            return _public_preview(preview)

    def close_preview(self, preview_id: str) -> None:
        with self._lock:
            preview = self._require_preview(preview_id)
            if preview["status"] != "ready":
                raise ValueError("这份预览还在处理")
            self._previews = [item for item in self._previews if item["id"] != preview_id]
            shutil.rmtree(self.root / "previews" / preview_id, ignore_errors=True)
            self._save_previews()

    def preview_action(self, preview_id: str, action: str, page: int, params) -> dict:
        if action not in PREVIEW_ACTIONS:
            raise ValueError("未知操作")
        if isinstance(page, bool) or not isinstance(page, int):
            raise ValueError("页码须是从 1 开始的正整数")
        watermark = ""
        if action == "watermark":
            if not isinstance(params, dict):
                raise ValueError("参数不正确")
            watermark = params.get("watermark_text")
            if not isinstance(watermark, str) or not watermark.strip():
                raise ValueError("请填写水印文字")
            watermark = watermark.strip()
            if len(watermark) > 80:
                raise ValueError("水印文字不能超过 80 个字")
        with self._lock:
            preview = self._require_preview(preview_id)
            if preview["status"] != "ready":
                raise ValueError("这份预览还在处理")
            if page < 1 or page > preview["page_count"]:
                raise ValueError(f"页码 {page} 超出范围（PDF共 {preview['page_count']} 页）")
            if action == "delete" and preview["page_count"] < 2:
                raise ValueError("不能删除全部页面")
            task_id = _new_id()
            item_id = _new_id()
            label = PREVIEW_ACTIONS[action]
            item = _blank_item(item_id, f"第 {page} 页 · {label}")
            task_dir = self.root / task_id / item_id
            task_dir.mkdir(parents=True, exist_ok=True)
            preview["status"] = "busy"
            preview["error"] = ""
            preview["action"] = action
            preview["action_page"] = page
            task = {
                "id": task_id,
                "tool": "preview",
                "preview_id": preview_id,
                "preview_name": preview["name"],
                "action": action,
                "page": page,
                "params": {"watermark_text": watermark, "angle": 90},
                "status": QUEUED,
                "stop_requested": False,
                "created_at": _now(),
                "finished_at": None,
                "error": "",
                "inputs": [{"name": preview["name"]}],
                "sources": [],
                "items": [item],
            }
            self._tasks.append(task)
            self._save()
            self._save_previews()
            public = _public_preview(preview)
        self._wake.set()
        return public

    def preview_file(self, preview_id: str) -> tuple[Path, str]:
        with self._lock:
            preview = self._require_preview(preview_id)
            path = self.root / "previews" / preview_id / "source.pdf"
            name = preview["name"]
        if not path.is_file():
            raise ValueError("预览不存在")
        return path, name

    def preview_image(self, preview_id: str, page: int) -> Path:
        with self._lock:
            preview = self._require_preview(preview_id)
            if page < 1 or page > preview["page_count"]:
                raise ValueError("这一页不存在")
            revision = preview["revision"]
            source = self.root / "previews" / preview_id / "source.pdf"
        cache = source.parent / "cache" / str(revision) / f"{page}.png"
        if cache.is_file():
            return cache
        return self._render_preview_page(preview_id, source, page, revision, cache)

    def submit(self, tool: str, params, uploads: list[tuple[str, Path]]) -> dict:
        if tool not in TOOLS:
            raise ValueError("未知工具")
        if not uploads:
            raise ValueError("请选择 PDF 文件")
        if tool == "merge" and len(uploads) < 2:
            raise ValueError("合并至少需要两份 PDF")

        normalized = normalize_params(tool, params)
        for name, path in uploads:
            if not name.lower().endswith(".pdf") or not _is_pdf_file(path):
                raise ValueError(f"只接受 PDF 文件：{os.path.basename(name)}")

        task_id = _new_id()
        task_dir = self.root / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        inputs = []
        items = []
        try:
            if tool == "merge":
                input_dir = task_dir / "inputs"
                input_dir.mkdir(parents=True, exist_ok=True)
                sources = []
                for index, (name, path) in enumerate(uploads):
                    target = input_dir / f"{index}.pdf"
                    shutil.move(str(path), str(target))
                    inputs.append({"name": os.path.basename(name)})
                    sources.append(f"{task_id}/inputs/{index}.pdf")
                item_id = _new_id()
                item = _blank_item(item_id, f"{_stem(uploads[0][0])}_merged.pdf")
                items.append(item)
                task_sources = sources
            else:
                task_sources = []
                for name, path in uploads:
                    item_id = _new_id()
                    item_dir = task_dir / item_id
                    item_dir.mkdir(parents=True, exist_ok=True)
                    stored_name = f"{_stem(name)}.pdf"
                    shutil.move(str(path), str(item_dir / stored_name))
                    item = _blank_item(item_id, os.path.basename(name))
                    item["source"] = f"{task_id}/{item_id}/{stored_name}"
                    items.append(item)
                    inputs.append({"name": item["name"]})
        except Exception:
            shutil.rmtree(task_dir, ignore_errors=True)
            raise

        task = {
            "id": task_id,
            "tool": tool,
            "params": normalized,
            "status": QUEUED,
            "stop_requested": False,
            "created_at": _now(),
            "finished_at": None,
            "error": "",
            "inputs": inputs,
            "sources": task_sources,
            "items": items,
        }
        with self._lock:
            self._tasks.append(task)
            self._save()
            public = _public_task(task)
        self._wake.set()
        return public

    def cancel(self, task_id: str) -> dict:
        with self._lock:
            task = self._require(task_id)
            if task["status"] == QUEUED:
                task["status"] = CANCELLED
                task["finished_at"] = _now()
                for item in task["items"]:
                    item["status"] = CANCELLED
                _forget_password(task)
                self._release_preview(task)
                self._save()
                return _public_task(task)
            if task["status"] == RUNNING:
                task["stop_requested"] = True
                self._save()
                return _public_task(task)
            raise ValueError("这个任务已经结束")

    def delete_item(self, task_id: str, item_id: str) -> None:
        with self._lock:
            task = self._require(task_id)
            if task["status"] not in TERMINAL:
                raise ValueError("任务还在进行，不能删除其中一份")
            item = self._require_item(task, item_id)
            if item["status"] != COMPLETED or not item["output"]:
                raise ValueError("这份还不能删除")
            self._delete_output(item)
            shutil.rmtree(self.root / task_id / item_id, ignore_errors=True)
            task["items"] = [current for current in task["items"] if current["id"] != item_id]
            if not task["items"]:
                self._tasks = [current for current in self._tasks if current["id"] != task_id]
                shutil.rmtree(self.root / task_id, ignore_errors=True)
            self._save()

    def output_file(self, task_id: str, item_id: str) -> tuple[Path, str]:
        with self._lock:
            task = self._require(task_id)
            item = self._require_item(task, item_id)
            if item["status"] != COMPLETED or not item["output"]:
                raise ValueError("结果不存在")
            path = self._under_root(item["output"])
            if not path.is_file():
                raise ValueError("结果不存在")
            return path, item["download_name"] or path.name

    def text_file(self, task_id: str, item_id: str) -> Path:
        with self._lock:
            task = self._require(task_id)
            if task["tool"] != "to_text":
                raise ValueError("结果不存在")
            item = self._require_item(task, item_id)
            if not item["preview"] or item["status"] != COMPLETED or not item["output"]:
                raise ValueError("结果不存在")
            path = self._under_root(item["output"])
        if not path.is_file():
            raise ValueError("结果不存在")
        return path

    def image_file(self, task_id: str, item_id: str, index: int) -> Path:
        with self._lock:
            task = self._require(task_id)
            if task["tool"] != "to_image":
                raise ValueError("结果不存在")
            item = self._require_item(task, item_id)
            images = item.get("images") or []
            if not item["preview"] or item["status"] != COMPLETED or index < 1 or index > len(images):
                raise ValueError("结果不存在")
            path = self._under_root(images[index - 1])
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg") or not path.is_file():
            raise ValueError("结果不存在")
        return path

    def close(self) -> None:
        self._closing = True
        with self._lock:
            for task in self._tasks:
                if task["status"] == RUNNING:
                    task["stop_requested"] = True
            self._save()
        self._wake.set()
        try:
            self._thread.join(timeout=120)
        except KeyboardInterrupt:
            with self._lock:
                self._recover()
            raise
        with self._lock:
            self._recover()

    def _loop(self) -> None:
        while not self._closing:
            self._expire()
            task_id = self._claim()
            if task_id is None:
                self._wake.wait(timeout=0.5)
                self._wake.clear()
                continue
            try:
                self._run(task_id)
            except Exception as exc:
                self._fail_task(task_id, str(exc))

    def _claim(self) -> str | None:
        with self._lock:
            if self._closing:
                return None
            for task in self._tasks:
                if task["status"] == QUEUED:
                    task["status"] = RUNNING
                    self._save()
                    return task["id"]
        return None

    def _run(self, task_id: str) -> None:
        while True:
            step = self._next_step(task_id)
            if step is None:
                self._finish(task_id)
                return
            if step == "stop":
                self._cancel_pending(task_id)
                self._finish(task_id)
                return
            try:
                result = self._execute(task_id, step)
            except ConversionStopped:
                self._mark_item(task_id, step["item_id"], STOPPED, "")
                self._cancel_pending(task_id)
                self._finish(task_id)
                return
            except Exception as exc:
                self._mark_item(task_id, step["item_id"], FAILED, str(exc))
                continue
            if self._stop_requested(task_id):
                self._discard_output(result.get("output", ""))
                self._mark_item(task_id, step["item_id"], STOPPED, "")
                self._cancel_pending(task_id)
                self._finish(task_id)
                return
            if step["tool"] == "preview":
                self._apply_preview(step, result)
            self._mark_item(task_id, step["item_id"], COMPLETED, "", result)

    def _next_step(self, task_id: str):
        with self._lock:
            task = self._find(task_id)
            if task is None or task["status"] != RUNNING:
                return None
            if task["stop_requested"]:
                return "stop"
            for item in task["items"]:
                if item["status"] == PENDING:
                    item["status"] = RUNNING
                    self._save()
                    return {
                        "item_id": item["id"],
                        "name": item["name"],
                        "tool": task["tool"],
                        "params": dict(task["params"]),
                        "source": item.get("source", ""),
                        "sources": list(task.get("sources", [])),
                        "preview_id": task.get("preview_id") or "",
                        "action": task.get("action") or "",
                        "page": task.get("page") or 0,
                        "preview_name": task.get("preview_name") or "",
                    }
        return None

    def _execute(self, task_id: str, step: dict) -> dict:
        tool = step["tool"]
        params = step["params"]
        item_dir = self.root / task_id / step["item_id"]
        out_dir = item_dir / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            if tool == "preview":
                return self._run_preview(step, out_dir)
            if tool == "merge":
                return self._run_merge(step, out_dir)
            source = self._under_root(step["source"])
            if tool == "to_text":
                return self._run_text(task_id, step, source, out_dir)
            if tool == "to_image":
                return self._run_images(step, source, out_dir)
            if tool == "split":
                return self._run_split(step, source, out_dir)
            if tool == "delete":
                return self._run_delete(step, source, out_dir)
            if tool == "compress":
                return self._run_compress(step, source, out_dir)
            if tool == "to_word":
                return self._run_word(task_id, step, source, out_dir)
            if tool == "to_excel":
                return self._run_excel(task_id, step, source, out_dir)
            if tool == "rotate":
                return self._run_rotate(step, source, out_dir)
            if tool == "watermark":
                return self._run_watermark(step, source, out_dir)
            if tool == "encrypt":
                return self._run_encrypt(step, source, out_dir)
            if tool == "decrypt":
                return self._run_decrypt(step, source, out_dir)
            raise ValueError("未知工具")
        except Exception:
            shutil.rmtree(out_dir, ignore_errors=True)
            raise

    def _run_text(self, task_id: str, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        item_id = step["item_id"]
        page_count = pdf_page_count(str(source))
        skip_pages = _text_skip_indexes(
            page_count, params["page_start"], params["page_end"], params["skip_pages"]
        )

        def on_page(page: int, total: int) -> None:
            self._set_progress(task_id, item_id, page, total)

        def on_page_error(page: int, message: str) -> None:
            self._add_page_error(task_id, item_id, page, message)

        def should_continue() -> bool:
            return not self._stop_requested(task_id)

        txt_path = convert_pdf_to_text(
            str(source),
            output_dir=str(out_dir),
            skip_pages=skip_pages,
            min_text_length=params["min_text_length"],
            on_page=on_page,
            on_page_error=on_page_error,
            should_continue=should_continue,
        )
        path = Path(txt_path)
        return {
            "output": path.relative_to(self.root).as_posix(),
            "download_name": f"{_stem(step['name'])}.txt",
            "preview": True,
            "ratio": None,
        }

    def _run_images(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        image_dir = out_dir / "images"
        saved = convert_pdf_to_images(
            str(source),
            output_dir=str(image_dir),
            image_format=params["image_format"],
            dpi=params["dpi"],
            start_page=first,
            end_page=last,
        )
        if not saved:
            raise ValueError("没有生成图片")
        download_name = f"{_stem(step['name'])}.zip"
        zip_path = out_dir / download_name
        self._zip_files([Path(path) for path in saved], zip_path)
        images = [Path(path).resolve().relative_to(self.root.resolve()).as_posix() for path in saved]
        payload = self._file_result(zip_path, download_name)
        payload["preview"] = True
        payload["images"] = images
        return payload

    def _run_split(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        piece_dir = out_dir / "pieces"
        saved = split_pdf(
            str(source),
            output_dir=str(piece_dir),
            pages_per_file=params["pages_per_file"],
            start_page=first,
            end_page=last,
        )
        if not saved:
            raise ValueError("没有生成文件")
        download_name = f"{_stem(step['name'])}.zip"
        zip_path = out_dir / download_name
        self._zip_files([Path(path) for path in saved], zip_path)
        shutil.rmtree(piece_dir, ignore_errors=True)
        return self._file_result(zip_path, download_name)

    def _run_delete(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        pages = [page for page in params["delete_pages"] if first <= page <= last]
        if not pages:
            raise ValueError("没有可删除的页面")
        if len(pages) >= (last - first + 1):
            raise ValueError("不能删除全部页面")
        download_name = f"{_stem(step['name'])}_deleted.pdf"
        output = out_dir / download_name
        delete_pages(str(source), pages, output_path=str(output), start_page=first, end_page=last)
        return self._file_result(output, download_name)

    def _run_compress(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        download_name = f"{_stem(step['name'])}_compressed.pdf"
        output = out_dir / download_name
        result = compress_pdf(
            str(source),
            output_path=str(output),
            compression_level=params["compression_level"],
            start_page=first,
            end_page=last,
        )
        payload = self._file_result(output, download_name)
        payload["ratio"] = round(float(result["compression_ratio"]), 1)
        return payload

    def _run_word(self, task_id: str, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        item_id = step["item_id"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])

        def on_page(page: int, total: int) -> None:
            self._set_progress(task_id, item_id, page, total)

        def on_page_error(page: int, message: str) -> None:
            self._add_page_error(task_id, item_id, page, message)

        def should_continue() -> bool:
            return not self._stop_requested(task_id)

        download_name = f"{_stem(step['name'])}.docx"
        output = out_dir / download_name
        convert_pdf_to_word(
            str(source),
            output_path=str(output),
            include_images=params["include_images"],
            start_page=first,
            end_page=last,
            on_page=on_page,
            on_page_error=on_page_error,
            should_continue=should_continue,
        )
        return self._file_result(output, download_name)

    def _run_excel(self, task_id: str, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        item_id = step["item_id"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])

        def on_page(page: int, total: int) -> None:
            self._set_progress(task_id, item_id, page, total)

        def on_page_error(page: int, message: str) -> None:
            self._add_page_error(task_id, item_id, page, message)

        def should_continue() -> bool:
            return not self._stop_requested(task_id)

        download_name = f"{_stem(step['name'])}.xlsx"
        output = out_dir / download_name
        convert_pdf_to_excel(
            str(source),
            output_path=str(output),
            table_only=params["table_only"],
            start_page=first,
            end_page=last,
            on_page=on_page,
            on_page_error=on_page_error,
            should_continue=should_continue,
        )
        return self._file_result(output, download_name)

    def _run_rotate(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        download_name = f"{_stem(step['name'])}_rotated.pdf"
        output = out_dir / download_name
        rotate_pdf(
            str(source),
            angle=params["angle"],
            output_path=str(output),
            start_page=first,
            end_page=last,
        )
        return self._file_result(output, download_name)

    def _run_watermark(self, step: dict, source: Path, out_dir: Path) -> dict:
        params = step["params"]
        page_count = pdf_page_count(str(source))
        first, last = _resolve_range(page_count, params["page_start"], params["page_end"])
        download_name = f"{_stem(step['name'])}_watermarked.pdf"
        output = out_dir / download_name
        add_watermark(
            str(source),
            params["watermark_text"],
            output_path=str(output),
            start_page=first,
            end_page=last,
        )
        return self._file_result(output, download_name)

    def _run_encrypt(self, step: dict, source: Path, out_dir: Path) -> dict:
        download_name = f"{_stem(step['name'])}_encrypted.pdf"
        output = out_dir / download_name
        encrypt_pdf(str(source), step["params"]["password"], output_path=str(output))
        return self._file_result(output, download_name)

    def _run_decrypt(self, step: dict, source: Path, out_dir: Path) -> dict:
        download_name = f"{_stem(step['name'])}_decrypted.pdf"
        output = out_dir / download_name
        decrypt_pdf(str(source), step["params"]["password"], output_path=str(output))
        return self._file_result(output, download_name)

    def _run_preview(self, step: dict, out_dir: Path) -> dict:
        action = step["action"]
        page = step["page"]
        source = self.root / "previews" / step["preview_id"] / "source.pdf"
        if not source.is_file():
            raise FileNotFoundError("预览不存在")
        if action == "text":
            text = _page_text(str(source), page)
            output = out_dir / "page.txt"
            output.write_text(text, encoding="utf-8")
            result = self._file_result(output, "page.txt")
            result["preview"] = True
            result["preview_text"] = text
            result["preview_kind"] = "text"
            return result
        output = out_dir / f"{_stem(step['preview_name'])}.pdf"
        if action == "rotate":
            rotate_pdf(str(source), angle=90, output_path=str(output), start_page=page, end_page=page)
        elif action == "watermark":
            add_watermark(
                str(source),
                step["params"]["watermark_text"],
                output_path=str(output),
                start_page=page,
                end_page=page,
            )
        elif action == "delete":
            delete_pages(str(source), [page], output_path=str(output))
        else:
            raise ValueError("未知操作")
        result = self._file_result(output, output.name)
        result["preview_kind"] = "file"
        return result

    def _apply_preview(self, step: dict, result: dict) -> None:
        with self._lock:
            preview = self._find_preview(step["preview_id"])
            if preview is None:
                return
            if result.get("preview_kind") == "text":
                preview["text"] = result.get("preview_text") or ""
                preview["text_page"] = step["page"]
                preview["last_action"] = "text"
                preview["last_page"] = step["page"]
                preview["error"] = ""
                preview["updated_at"] = _now()
                self._save_previews()
                return
            output = self._under_root(result["output"])
            page_count = _pdf_page_count(output)
            directory = self.root / "previews" / preview["id"]
            temporary = directory / "source.tmp.pdf"
            shutil.copyfile(output, temporary)
            os.replace(temporary, directory / "source.pdf")
            shutil.rmtree(directory / "cache", ignore_errors=True)
            preview["page_count"] = page_count
            preview["revision"] += 1
            preview["text"] = ""
            preview["text_page"] = 0
            preview["last_action"] = step["action"]
            preview["last_page"] = step["page"]
            preview["error"] = ""
            preview["updated_at"] = _now()
            self._save_previews()

    def _render_preview_page(self, preview_id: str, source: Path, page: int, revision: int, cache: Path) -> Path:
        import fitz

        cache.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache.with_suffix(".tmp.png")
        doc = fitz.open(source)
        try:
            pixmap = doc[page - 1].get_pixmap(dpi=PREVIEW_DPI, alpha=False)
            pixmap.save(str(temporary))
        finally:
            doc.close()
        with self._lock:
            preview = self._find_preview(preview_id)
            if preview is None or preview["revision"] != revision:
                temporary.unlink(missing_ok=True)
                raise ValueError("这一页已更新")
            os.replace(temporary, cache)
        return cache

    def _run_merge(self, step: dict, out_dir: Path) -> dict:
        sources = [str(self._under_root(rel)) for rel in step["sources"]]
        download_name = step["name"]
        output = out_dir / download_name
        merge_pdfs(sources, output_path=str(output))
        return self._file_result(output, download_name)

    def _file_result(self, path: Path, download_name: str) -> dict:
        return {
            "output": path.relative_to(self.root).as_posix(),
            "download_name": download_name,
            "preview": False,
            "ratio": None,
        }

    def _zip_files(self, paths: list[Path], zip_path: Path) -> None:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            wrote = False
            for path in paths:
                if path.is_file():
                    archive.write(path, path.name)
                    wrote = True
        if not wrote:
            raise ValueError("没有生成文件")

    def _set_progress(self, task_id: str, item_id: str, page: int, total: int) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return
            item = self._find_item(task, item_id)
            if item is None:
                return
            item["page"] = page
            item["page_count"] = total
            self._save()

    def _add_page_error(self, task_id: str, item_id: str, page: int, message: str) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return
            item = self._find_item(task, item_id)
            if item is None:
                return
            item["page_errors"].append({"page": page, "message": message[:300]})
            self._save()

    def _stop_requested(self, task_id: str) -> bool:
        with self._lock:
            task = self._find(task_id)
            return bool(task and task["stop_requested"])

    def _mark_item(self, task_id: str, item_id: str, status: str, error: str, result: dict | None = None) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return
            item = self._find_item(task, item_id)
            if item is None:
                return
            item["status"] = status
            item["error"] = error
            if result:
                item["output"] = result["output"]
                item["download_name"] = result["download_name"]
                item["preview"] = result["preview"]
                item["images"] = list(result.get("images") or [])
                item["ratio"] = result["ratio"]
            self._save()

    def _cancel_pending(self, task_id: str) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return
            for item in task["items"]:
                if item["status"] == PENDING:
                    item["status"] = CANCELLED
            self._save()

    def _discard_output(self, relative: str) -> None:
        if not relative:
            return
        try:
            path = self._under_root(relative)
        except ValueError:
            return
        if path.is_file():
            path.unlink()
        parent = path.parent
        if parent.name == "out":
            shutil.rmtree(parent, ignore_errors=True)

    def _delete_output(self, item: dict) -> None:
        self._discard_output(item.get("output", ""))
        item["output"] = ""
        item["preview"] = False
        item["images"] = []

    def _finish(self, task_id: str) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None or task["status"] != RUNNING:
                return
            statuses = [item["status"] for item in task["items"]]
            if task["stop_requested"]:
                task["status"] = STOPPED
            elif statuses and all(status == CANCELLED for status in statuses):
                task["status"] = CANCELLED
            elif any(status == COMPLETED for status in statuses):
                task["status"] = COMPLETED
            else:
                task["status"] = FAILED
            task["finished_at"] = _now()
            _forget_password(task)
            self._release_preview(task)
            self._save()

    def _fail_task(self, task_id: str, message: str) -> None:
        with self._lock:
            task = self._find(task_id)
            if task is None:
                return
            for item in task["items"]:
                if item["status"] in (PENDING, RUNNING):
                    if item["status"] == RUNNING:
                        self._clear_item_dir(task_id, item["id"])
                    item["status"] = FAILED
                    item["error"] = message
            task["status"] = FAILED
            task["error"] = message
            task["finished_at"] = _now()
            _forget_password(task)
            self._release_preview(task)
            self._save()

    def _recover(self) -> None:
        kept = []
        for task in self._tasks:
            if task["status"] == QUEUED:
                shutil.rmtree(self.root / task["id"], ignore_errors=True)
                continue
            if task["status"] == RUNNING:
                completed = False
                for item in task["items"]:
                    if item["status"] == COMPLETED:
                        completed = True
                    elif item["status"] == RUNNING:
                        self._clear_item_dir(task["id"], item["id"])
                        item["status"] = FAILED
                        item["error"] = "网页已关闭，这一份没有做完"
                        item["output"] = ""
                        item["preview"] = False
                        item["images"] = []
                    elif item["status"] == PENDING:
                        item["status"] = CANCELLED
                        item["error"] = "网页已关闭，未继续"
                task["status"] = COMPLETED if completed else FAILED
                task["stop_requested"] = False
                task["finished_at"] = task["finished_at"] or _now()
            _forget_password(task)
            kept.append(task)
        self._tasks = kept
        self._recover_previews()
        self._save()

    def _expire(self) -> None:
        now = datetime.now()
        if now - self._expired_at < timedelta(minutes=1):
            return
        self._expired_at = now
        with self._lock:
            kept = []
            changed = False
            for task in self._tasks:
                if _past_retention(task, now):
                    directory = self._task_dir(str(task.get("id") or ""))
                    if directory is not None:
                        shutil.rmtree(directory, ignore_errors=True)
                    changed = True
                    continue
                kept.append(task)
            if changed:
                self._tasks = kept
            if self._expire_previews(now):
                self._save_previews()
            self._sweep_orphans(now)
            if changed:
                self._save()

    def _task_dir(self, task_id: str) -> Path | None:
        if not task_id or task_id in (".", "..") or "/" in task_id or "\\" in task_id:
            return None
        root = self.root.resolve()
        path = (root / task_id).resolve()
        if path.parent != root:
            return None
        return path

    def _sweep_orphans(self, now: datetime) -> None:
        known = {task["id"] for task in self._tasks}
        try:
            children = list(self.root.iterdir())
        except OSError:
            return
        for child in children:
            if child.name == "previews" and child.is_dir():
                self._sweep_preview_dirs(now)
                continue
            if child.name in known or child.name in ("tasks.json", "tasks.json.tmp") or not child.is_dir():
                continue
            try:
                modified = datetime.fromtimestamp(child.stat().st_mtime)
            except OSError:
                continue
            if now - modified > RETENTION:
                shutil.rmtree(child, ignore_errors=True)

    def _release_preview(self, task: dict) -> None:
        preview_id = task.get("preview_id") or ""
        if not preview_id:
            return
        preview = self._find_preview(preview_id)
        if preview is None:
            return
        preview["status"] = "ready"
        preview["action"] = ""
        if task["status"] in (FAILED, STOPPED):
            message = task.get("error") or ""
            if not message:
                for item in task["items"]:
                    if item.get("error"):
                        message = item["error"]
                        break
            if not message and task["status"] == STOPPED:
                message = "已停止"
            if message:
                preview["error"] = message
        self._save_previews()

    def _recover_previews(self) -> None:
        active = {
            task.get("preview_id")
            for task in self._tasks
            if task.get("preview_id") and task.get("status") in (QUEUED, RUNNING)
        }
        changed = False
        for preview in self._previews:
            if preview.get("status") == "busy" and preview["id"] not in active:
                preview["status"] = "ready"
                preview["action"] = ""
                if not preview.get("error"):
                    preview["error"] = "网页已关闭，这一步没有做完"
                changed = True
        if changed:
            self._save_previews()

    def _expire_previews(self, now: datetime) -> bool:
        kept = []
        changed = False
        for preview in self._previews:
            if preview.get("status") == "busy":
                kept.append(preview)
                continue
            stamp = preview.get("updated_at") or preview.get("created_at")
            record = {"status": COMPLETED, "finished_at": stamp, "created_at": stamp}
            if _past_retention(record, now):
                shutil.rmtree(self.root / "previews" / str(preview.get("id") or ""), ignore_errors=True)
                changed = True
                continue
            kept.append(preview)
        if changed:
            self._previews = kept
        return changed

    def _sweep_preview_dirs(self, now: datetime) -> None:
        directory = self.root / "previews"
        known = {preview["id"] for preview in self._previews}
        try:
            children = list(directory.iterdir())
        except OSError:
            return
        for child in children:
            if child.name in known or not child.is_dir():
                continue
            try:
                modified = datetime.fromtimestamp(child.stat().st_mtime)
            except OSError:
                continue
            if now - modified > RETENTION:
                shutil.rmtree(child, ignore_errors=True)

    def _find_preview(self, preview_id: str) -> dict | None:
        for preview in self._previews:
            if preview["id"] == preview_id:
                return preview
        return None

    def _require_preview(self, preview_id: str) -> dict:
        preview = self._find_preview(preview_id)
        if preview is None:
            raise ValueError("找不到这份预览")
        return preview

    def _load_previews(self) -> None:
        if not self._preview_path.is_file():
            self._previews = []
            return
        try:
            data = json.loads(self._preview_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._previews = []
            return
        self._previews = data.get("previews", []) if isinstance(data, dict) else []

    def _save_previews(self) -> None:
        payload = json.dumps({"previews": self._previews}, ensure_ascii=False, indent=2)
        temporary = self._preview_path.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self._preview_path)

    def _clear_item_dir(self, task_id: str, item_id: str) -> None:
        shutil.rmtree(self.root / task_id / item_id / "out", ignore_errors=True)

    def _load(self) -> None:
        if not self._path.is_file():
            self._tasks = []
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._tasks = []
            return
        self._tasks = data.get("tasks", []) if isinstance(data, dict) else []

    def _save(self) -> None:
        payload = json.dumps({"tasks": self._tasks}, ensure_ascii=False, indent=2)
        temporary = self._path.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self._path)

    def _find(self, task_id: str) -> dict | None:
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def _require(self, task_id: str) -> dict:
        task = self._find(task_id)
        if task is None:
            raise ValueError("找不到这个任务")
        return task

    def _find_item(self, task: dict, item_id: str) -> dict | None:
        for item in task["items"]:
            if item["id"] == item_id:
                return item
        return None

    def _require_item(self, task: dict, item_id: str) -> dict:
        item = self._find_item(task, item_id)
        if item is None:
            raise ValueError("找不到这份结果")
        return item

    def _under_root(self, relative: str) -> Path:
        root = self.root.resolve()
        path = (root / relative).resolve()
        if path != root and root not in path.parents:
            raise ValueError("路径无效")
        return path
