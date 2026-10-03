from __future__ import annotations

import io
import json
import os
import re
import socket
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.engine import Workbench

HOST = "0.0.0.0"
PORT = 8765
STATIC_DIR = Path(__file__).resolve().parent / "static"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class RequestBody:
    def __init__(self, stream, length: int):
        self.stream = stream
        self.left = length
        self.buffer = b""

    def read(self, size: int) -> bytes:
        while len(self.buffer) < size and self.left > 0:
            piece = self.stream.read(min(1024 * 1024, self.left))
            if not piece:
                break
            self.left -= len(piece)
            self.buffer += piece
        size = min(size, len(self.buffer))
        data = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return data

    def readline(self) -> bytes:
        while b"\n" not in self.buffer and self.left > 0:
            piece = self.stream.read(min(8192, self.left))
            if not piece:
                break
            self.left -= len(piece)
            self.buffer += piece
        index = self.buffer.find(b"\n")
        if index == -1:
            data = self.buffer
            self.buffer = b""
            return data
        data = self.buffer[: index + 1]
        self.buffer = self.buffer[index + 1 :]
        return data

    def push(self, data: bytes) -> None:
        self.buffer = data + self.buffer


def _disposition(header_text: str) -> tuple[str, str | None]:
    name_match = re.search(r'name="([^"]*)"', header_text)
    name = name_match.group(1) if name_match else ""
    encoded = re.search(r"filename\*=UTF-8''([^;\r\n]+)", header_text, re.I)
    if encoded:
        return name, unquote(encoded.group(1))
    quoted = re.search(r'filename="([^"]*)"', header_text)
    if quoted:
        return name, quoted.group(1)
    plain = re.search(r"filename=([^;\r\n]+)", header_text)
    if plain:
        return name, plain.group(1).strip().strip('"')
    return name, None


def _copy_until(body: RequestBody, boundary: bytes, output) -> bool:
    token = b"\r\n--" + boundary
    tail = b""
    while True:
        chunk = body.read(65536)
        data = tail + chunk
        index = data.find(token)
        if index == -1:
            if not chunk:
                raise ValueError("请求内容不完整")
            keep = max(len(token) - 1, 0)
            if len(data) > keep:
                output.write(data[:-keep])
                tail = data[-keep:]
            else:
                tail = data
            continue
        output.write(data[:index])
        body.push(data[index + len(token) :])
        marker = body.read(2)
        if marker == b"--":
            return True
        if marker == b"\r\n":
            return False
        if marker.startswith(b"\n"):
            body.push(marker[1:])
            return False
        raise ValueError("请求内容不正确")


def parse_form(stream, length: int, content_type: str, directory: Path) -> tuple[dict, list]:
    match = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type or "")
    if not match:
        raise ValueError("请求内容不正确")
    boundary = (match.group(1) or match.group(2) or "").strip().encode("ascii", "strict")
    body = RequestBody(stream, length)
    opening = body.readline().rstrip(b"\r\n")
    if opening != b"--" + boundary:
        raise ValueError("请求内容不正确")

    fields = {}
    files = []
    while True:
        headers = []
        while True:
            line = body.readline()
            if line in (b"\r\n", b"\n"):
                break
            if line == b"":
                raise ValueError("请求内容不完整")
            headers.append(line.decode("utf-8", "replace"))
        name, filename = _disposition("".join(headers))
        if filename is not None:
            target = directory / f"part-{len(files)}.bin"
            with target.open("wb") as handle:
                closing = _copy_until(body, boundary, handle)
            files.append((os.path.basename(filename), target))
        else:
            buffer = io.BytesIO()
            closing = _copy_until(body, boundary, buffer)
            fields[name] = buffer.getvalue().decode("utf-8")
        if closing:
            break
    return fields, files


def lan_urls(port: int) -> list[str]:
    found = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        found.add(probe.getsockname()[0])
    except OSError:
        pass
    finally:
        probe.close()
    addresses = sorted(ip for ip in found if ip and not ip.startswith("127."))
    return [f"http://{ip}:{port}" for ip in addresses]


def _content_type(path: Path) -> str:
    return CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


class Handler(BaseHTTPRequestHandler):
    server_version = "pdf-workbench"

    def log_message(self, fmt, *args):
        path = urlparse(self.path).path
        if path == "/api/state":
            return
        super().log_message(fmt, *args)

    def do_GET(self):
        try:
            self._get()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"处理失败：{exc}"})

    def do_POST(self):
        try:
            self._post()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"处理失败：{exc}"})

    def do_DELETE(self):
        try:
            self._delete()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"处理失败：{exc}"})

    def _get(self):
        path = unquote(urlparse(self.path).path)
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == "/api/state":
            self._json(
                200,
                {
                    "local": f"http://127.0.0.1:{PORT}",
                    "lan": lan_urls(PORT),
                    "tasks": self.server.workbench.snapshot(),
                    "previews": self.server.workbench.preview_snapshot(),
                },
            )
            return
        preview_page = re.fullmatch(r"/api/previews/([0-9a-f]+)/pages/([1-9][0-9]*)", path)
        if preview_page:
            file_path = self.server.workbench.preview_image(preview_page.group(1), int(preview_page.group(2)))
            self._send_path(file_path, file_path.name, attachment=False, cache=False)
            return
        preview_file = re.fullmatch(r"/api/previews/([0-9a-f]+)/download", path)
        if preview_file:
            file_path, name = self.server.workbench.preview_file(preview_file.group(1))
            self._send_path(file_path, name, attachment=True)
            return
        download = re.fullmatch(r"/api/tasks/([0-9a-f]+)/items/([0-9a-f]+)/download", path)
        if download:
            file_path, name = self.server.workbench.output_file(download.group(1), download.group(2))
            self._send_path(file_path, name, attachment=True)
            return
        text = re.fullmatch(r"/api/tasks/([0-9a-f]+)/items/([0-9a-f]+)/text", path)
        if text:
            file_path = self.server.workbench.text_file(text.group(1), text.group(2))
            self._send_path(file_path, file_path.name, attachment=False)
            return
        image = re.fullmatch(r"/api/tasks/([0-9a-f]+)/items/([0-9a-f]+)/images/([1-9][0-9]*)", path)
        if image:
            file_path = self.server.workbench.image_file(image.group(1), image.group(2), int(image.group(3)))
            self._send_path(file_path, file_path.name, attachment=False)
            return
        self._static(path)

    def _post(self):
        path = unquote(urlparse(self.path).path)
        if path == "/api/tasks":
            self._submit()
            return
        if path == "/api/previews":
            self._open_preview()
            return
        preview_action = re.fullmatch(r"/api/previews/([0-9a-f]+)/actions", path)
        if preview_action:
            payload = self._read_json()
            page = payload.get("page")
            preview = self.server.workbench.preview_action(
                preview_action.group(1),
                str(payload.get("action") or ""),
                page if isinstance(page, int) else -1,
                payload,
            )
            self._json(200, {"preview": preview})
            return
        cancel = re.fullmatch(r"/api/tasks/([0-9a-f]+)/cancel", path)
        if cancel:
            task = self.server.workbench.cancel(cancel.group(1))
            self._json(200, {"task": task})
            return
        self._json(404, {"error": "找不到页面"})

    def _delete(self):
        path = unquote(urlparse(self.path).path)
        preview = re.fullmatch(r"/api/previews/([0-9a-f]+)", path)
        if preview:
            self.server.workbench.close_preview(preview.group(1))
            self._json(200, {"ok": True})
            return
        match = re.fullmatch(r"/api/tasks/([0-9a-f]+)/items/([0-9a-f]+)", path)
        if not match:
            self._json(404, {"error": "找不到页面"})
            return
        self.server.workbench.delete_item(match.group(1), match.group(2))
        self._json(200, {"ok": True})

    def _submit(self):
        length = self.headers.get("Content-Length")
        if length is None or not length.isdigit():
            raise ValueError("请求内容不正确")
        with tempfile.TemporaryDirectory(prefix="pdf-workbench-") as temp_name:
            fields, files = parse_form(
                self.rfile,
                int(length),
                self.headers.get("Content-Type", ""),
                Path(temp_name),
            )
            try:
                params = json.loads(fields.get("params") or "{}")
            except json.JSONDecodeError as exc:
                raise ValueError("参数不正确") from exc
            task = self.server.workbench.submit(fields.get("tool", ""), params, files)
        self._json(200, {"task": task})

    def _open_preview(self):
        length = self.headers.get("Content-Length")
        if length is None or not length.isdigit():
            raise ValueError("请求内容不正确")
        with tempfile.TemporaryDirectory(prefix="pdf-workbench-") as temp_name:
            _fields, files = parse_form(
                self.rfile,
                int(length),
                self.headers.get("Content-Type", ""),
                Path(temp_name),
            )
            if len(files) != 1:
                raise ValueError("预览一次打开一份 PDF")
            name, path = files[0]
            preview = self.server.workbench.open_preview(name, path)
        self._json(200, {"preview": preview})

    def _read_json(self) -> dict:
        length = self.headers.get("Content-Length")
        if length is None or not length.isdigit():
            raise ValueError("请求内容不正确")
        try:
            payload = json.loads(self.rfile.read(int(length)).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("参数不正确") from exc
        if not isinstance(payload, dict):
            raise ValueError("参数不正确")
        return payload

    def _static(self, path: str):
        if path in ("/", "/index.html"):
            target = STATIC_DIR / "index.html"
        elif path.startswith("/static/"):
            target = (STATIC_DIR / path[len("/static/") :]).resolve()
            root = STATIC_DIR.resolve()
            if target != root and root not in target.parents:
                self._json(404, {"error": "找不到页面"})
                return
        else:
            self._json(404, {"error": "找不到页面"})
            return
        if not target.is_file():
            self._json(404, {"error": "找不到页面"})
            return
        self._send_path(target, target.name, attachment=False, cache=False)

    def _send_path(self, path: Path, name: str, attachment: bool, cache: bool = True):
        self.send_response(200)
        self.send_header("Content-Type", _content_type(path))
        self.send_header("Content-Length", str(path.stat().st_size))
        if not cache:
            self.send_header("Cache-Control", "no-cache")
        if attachment:
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(name)}")
        self.end_headers()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _json(self, status: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, workbench: Workbench):
        self.workbench = workbench
        super().__init__(address, Handler)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    workbench = Workbench()
    server = None
    try:
        server = WorkbenchServer((HOST, PORT), workbench)
        print(f"工作台已在这台电脑打开：http://127.0.0.1:{PORT}", flush=True)
        urls = lan_urls(PORT)
        for url in urls:
            print(f"局域网地址：{url}", flush=True)
        if not urls:
            print("当前没有局域网地址，只能在这台电脑上打开", flush=True)
        print("手机若打不开，请在 Windows 防火墙中允许此端口", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止，当前这一页会跑完")
    except OSError as exc:
        print(f"无法启动：{exc}")
    finally:
        try:
            workbench.close()
        except KeyboardInterrupt:
            os._exit(0)
        if server is not None:
            server.server_close()


if __name__ == "__main__":
    main()
