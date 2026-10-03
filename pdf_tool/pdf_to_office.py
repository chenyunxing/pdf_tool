import io
import os
import shutil
import tempfile


def _page_bounds(total_pages: int, start_page: int | None, end_page: int | None) -> tuple[int, int]:
    start = 1 if start_page is None else start_page
    end = total_pages if end_page is None else end_page
    if isinstance(start, bool) or not isinstance(start, int) or start < 1:
        raise ValueError("起始页须是从 1 开始的正整数")
    if isinstance(end, bool) or not isinstance(end, int) or end < 1:
        raise ValueError("结束页须是从 1 开始的正整数")
    if start > total_pages:
        raise ValueError(f"起始页 {start} 超出范围（PDF共 {total_pages} 页）")
    end = min(end, total_pages)
    if start > end:
        raise ValueError("没有可处理的页面")
    return start, end


def _overlaps(box, other, ratio: float = 0.6) -> bool:
    ax0, ay0, ax1, ay1 = box
    bx0, by0, bx1, by1 = other
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return False
    area = max((ax1 - ax0) * (ay1 - ay0), 1)
    return (ix1 - ix0) * (iy1 - iy0) / area >= ratio


def _page_tables(page):
    finder = getattr(page, "find_tables", None)
    if finder is None:
        return []
    try:
        found = finder()
    except (ValueError, RuntimeError):
        return []
    tables = list(getattr(found, "tables", []) or [])
    kept = []
    for table in tables:
        box = tuple(table.bbox)
        if any(_overlaps(box, tuple(other.bbox), 0.8) for other in kept):
            continue
        kept.append(table)
    return kept


def _text_lines(block) -> list[str]:
    lines = []
    for line in block.get("lines", []):
        text = "".join(span.get("text", "") for span in line.get("spans", []))
        if text.strip():
            lines.append(text.rstrip())
    return lines


def _page_items(doc, page, include_images: bool) -> list[dict]:
    try:
        raw = page.get_text("dict", sort=True)
    except TypeError:
        raw = page.get_text("dict")

    tables = _page_tables(page)
    table_boxes = [tuple(table.bbox) for table in tables]
    items = []
    for block in raw.get("blocks", []):
        bbox = tuple(block.get("bbox", (0, 0, 0, 0)))
        if any(_overlaps(bbox, box) for box in table_boxes):
            continue
        if block.get("type") == 1:
            if include_images:
                items.append({"kind": "image", "bbox": bbox, "block": block})
            continue
        lines = _text_lines(block)
        if lines:
            items.append({"kind": "text", "bbox": bbox, "lines": lines})

    for table in tables:
        rows = table.extract() or []
        items.append({"kind": "table", "bbox": tuple(table.bbox), "rows": rows})
    return _reading_order(items, page.rect.width)


def _reading_order(items: list[dict], page_width: float) -> list[dict]:
    if not items:
        return []
    positioned = _split_columns(items, page_width)
    left = positioned["left"]
    right = positioned["right"]
    if not left or not right:
        return _by_position(items)

    left_band = [item for item in left if any(_vertical_overlap(item, other) for other in right)]
    right_band = [item for item in right if any(_vertical_overlap(item, other) for other in left)]
    if not left_band or not right_band:
        return _by_position(items)

    paired = left_band + right_band
    band_top = min(item["bbox"][1] for item in paired)
    band_bottom = max(item["bbox"][3] for item in paired)

    band_ids = {id(item) for item in left_band + right_band}
    above = []
    below = []
    interrupting = []
    for item in items:
        if id(item) in band_ids:
            continue
        if item["bbox"][3] <= band_top:
            above.append(item)
        elif item["bbox"][1] >= band_bottom:
            below.append(item)
        else:
            interrupting.append(item)

    ordered = _by_position(above)
    if not interrupting:
        return ordered + _by_position(left_band) + _by_position(right_band) + _by_position(below)

    cursor = band_top
    for band in _by_position(interrupting):
        top = band["bbox"][1]
        ordered.extend(item for item in _by_position(left_band) if cursor <= item["bbox"][1] < top)
        ordered.extend(item for item in _by_position(right_band) if cursor <= item["bbox"][1] < top)
        ordered.append(band)
        cursor = band["bbox"][3]
    ordered.extend(item for item in _by_position(left_band) if item["bbox"][1] >= cursor)
    ordered.extend(item for item in _by_position(right_band) if item["bbox"][1] >= cursor)
    ordered.extend(_by_position(below))
    return ordered


def _split_columns(items: list[dict], page_width: float) -> dict:
    mid = page_width / 2
    columns = {"left": [], "right": [], "full": []}
    for item in items:
        x0, _, x1, _ = item["bbox"]
        crosses = x0 < mid - 36 and x1 > mid + 36
        if crosses or (x1 - x0) >= page_width * 0.72:
            columns["full"].append(item)
        elif x1 <= mid + 12:
            columns["left"].append(item)
        elif x0 >= mid - 12:
            columns["right"].append(item)
        else:
            columns["full"].append(item)
    return columns


def _vertical_overlap(one: dict, other: dict, slack: float = 6) -> bool:
    return one["bbox"][3] + slack > other["bbox"][1] and other["bbox"][3] + slack > one["bbox"][1]


def _by_position(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def _write_table(word_doc, rows) -> None:
    cleaned = []
    for row in rows or []:
        if not row:
            continue
        cleaned.append(["" if cell is None else str(cell).strip() for cell in row])
    width = max((len(row) for row in cleaned), default=0)
    if width == 0 or not any(any(cell for cell in row) for row in cleaned):
        return
    table = word_doc.add_table(rows=len(cleaned), cols=width)
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    for index, row in enumerate(cleaned):
        for column in range(width):
            table.rows[index].cells[column].text = row[column] if column < len(row) else ""


def _write_image(word_doc, doc, page, item) -> None:
    import fitz
    from docx.image.exceptions import UnrecognizedImageError
    from docx.shared import Inches

    block = item["block"]
    data = block.get("image")
    xref = block.get("xref")
    if not data and xref:
        try:
            data = doc.extract_image(xref).get("image")
        except (ValueError, RuntimeError):
            data = None
    if not data:
        clip = fitz.Rect(item["bbox"])
        if clip.is_empty or clip.is_infinite:
            return
        try:
            data = page.get_pixmap(clip=clip, dpi=120).tobytes("png")
        except (ValueError, RuntimeError):
            return
    if not data:
        return
    x0, _, x1, _ = item["bbox"]
    width = min(max((x1 - x0) / 72, 0.5), 6.3)
    try:
        word_doc.add_picture(io.BytesIO(data), width=Inches(width))
    except (OSError, ValueError, UnrecognizedImageError):
        return


SCAN_TEXT_LIMIT = 30
SCAN_IMAGE_RATIO = 0.45


def _compact_length(text: str) -> int:
    return len("".join(text.split()))


def _is_scan_page(page) -> bool:
    text_length = _compact_length(page.get_text("text"))
    if text_length >= SCAN_TEXT_LIMIT:
        return False
    area = page.rect.width * page.rect.height
    if area <= 0:
        return False
    images = page.get_images()
    if not images:
        return False
    if text_length == 0:
        return True
    for image in images:
        try:
            rects = page.get_image_rects(image[0])
        except (ValueError, RuntimeError):
            continue
        for rect in rects:
            if rect.width * rect.height >= area * SCAN_IMAGE_RATIO:
                return True
    return False


def _ocr_lines(boxes: list[dict], image_width: int) -> list[str]:
    items = []
    for box in boxes:
        text = str(box.get("text") or "").strip()
        if not text:
            continue
        left = float(box.get("left") or 0)
        top = float(box.get("top") or 0)
        right = float(box.get("right") or 0)
        bottom = float(box.get("bottom") or 0)
        if right <= left or bottom <= top:
            continue
        items.append({"kind": "text", "bbox": (left, top, right, bottom), "lines": [text]})
    lines = []
    for item in _reading_order(items, float(image_width or 1)):
        lines.extend(item["lines"])
    return lines


def _write_ocr_lines(word_doc, boxes: list[dict], image_width: int) -> None:
    for line in _ocr_lines(boxes, image_width):
        word_doc.add_paragraph(line)


def _write_page(word_doc, doc, page, include_images: bool) -> None:
    for item in _page_items(doc, page, include_images):
        if item["kind"] == "text":
            for line in item["lines"]:
                word_doc.add_paragraph(line)
        elif item["kind"] == "table":
            _write_table(word_doc, item["rows"])
        elif item["kind"] == "image":
            _write_image(word_doc, doc, page, item)


def _ensure_ocr(state: dict, prefix: str):
    if state["ocr"] is None:
        from .wechat_ocr import WeChatOCR

        state["ocr"] = WeChatOCR()
        state["dir"] = tempfile.mkdtemp(prefix=prefix)
    return state["ocr"], state["dir"]


def _recognize_lines(pdf_path: str, page_number: int, state: dict, prefix: str, on_page_error) -> list[str]:
    from .pdf_to_text import recognize_pdf_page

    ocr, image_dir = _ensure_ocr(state, prefix)
    print(f"识别第 {page_number} 页...")
    try:
        boxes, width = recognize_pdf_page(pdf_path, page_number, ocr, image_dir)
    except Exception as exc:
        print(f"第 {page_number} 页识别失败: {exc}")
        if on_page_error is not None:
            on_page_error(page_number, str(exc))
        return []
    return _ocr_lines(boxes, width)


def _write_scanned_page(word_doc, pdf_path: str, page_number: int, state: dict, on_page_error) -> None:
    for line in _recognize_lines(pdf_path, page_number, state, "pdf-word-", on_page_error):
        word_doc.add_paragraph(line)


def convert_pdf_to_word(
    pdf_path: str,
    output_path: str | None = None,
    include_images: bool = True,
    start_page: int | None = None,
    end_page: int | None = None,
    on_page=None,
    on_page_error=None,
    should_continue=None,
) -> str:
    import fitz
    from docx import Document
    from .pdf_to_text import ConversionStopped

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}.docx")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("读取PDF文件...")
    state = {"ocr": None, "dir": None}
    doc = fitz.open(pdf_path)
    try:
        first, last = _page_bounds(doc.page_count, start_page, end_page)
        word_doc = Document()
        print("提取文本和图片...")
        for page_num in range(first - 1, last):
            if should_continue is not None and not should_continue():
                raise ConversionStopped()
            page_number = page_num + 1
            if on_page is not None:
                on_page(page_number, doc.page_count)
            page = doc[page_num]
            if _is_scan_page(page):
                _write_scanned_page(word_doc, pdf_path, page_number, state, on_page_error)
            else:
                _write_page(word_doc, doc, page, include_images)
            if page_num < last - 1:
                word_doc.add_page_break()
        word_doc.save(output_path)
    finally:
        doc.close()
        if state["ocr"] is not None:
            state["ocr"].stop()
        if state["dir"] is not None:
            shutil.rmtree(state["dir"], ignore_errors=True)

    print(f"转换完成，结果保存到: {output_path}")
    return output_path


def _write_sheet_lines(ws, row_idx: int, page_number: int, lines: list[str]) -> int:
    if not lines:
        return row_idx
    ws.cell(row=row_idx, column=1, value=f"--- 第 {page_number} 页 ---")
    row_idx += 1
    for line in lines:
        ws.cell(row=row_idx, column=1, value=line)
        row_idx += 1
    return row_idx


def convert_pdf_to_excel(
    pdf_path: str,
    output_path: str | None = None,
    table_only: bool = False,
    start_page: int | None = None,
    end_page: int | None = None,
    on_page=None,
    on_page_error=None,
    should_continue=None,
) -> str:
    import fitz
    from openpyxl import Workbook
    from .pdf_to_text import ConversionStopped

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}.xlsx")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("读取PDF文件...")
    state = {"ocr": None, "dir": None}
    doc = fitz.open(pdf_path)
    try:
        first, last = _page_bounds(doc.page_count, start_page, end_page)
        wb = Workbook()
        ws = wb.active
        ws.title = "PDF内容"
        print("提取表格数据...")
        row_idx = 1
        for page_num in range(first - 1, last):
            if should_continue is not None and not should_continue():
                raise ConversionStopped()
            page_number = page_num + 1
            if on_page is not None:
                on_page(page_number, doc.page_count)
            page = doc[page_num]
            if _is_scan_page(page):
                lines = _recognize_lines(pdf_path, page_number, state, "pdf-excel-", on_page_error)
                row_idx = _write_sheet_lines(ws, row_idx, page_number, lines)
                row_idx += 2
                continue
            tables = _page_tables(page)
            for table in tables:
                for row in table.extract() or []:
                    if not row:
                        continue
                    for column, cell in enumerate(row):
                        ws.cell(row=row_idx, column=column + 1, value=cell)
                    row_idx += 1
                row_idx += 1

            if not table_only:
                text = page.get_text()
                if text.strip():
                    row_idx = _write_sheet_lines(
                        ws,
                        row_idx,
                        page_number,
                        [line.strip() for line in text.split("\n") if line.strip()],
                    )
            row_idx += 2
        wb.save(output_path)
    finally:
        doc.close()
        if state["ocr"] is not None:
            state["ocr"].stop()
        if state["dir"] is not None:
            shutil.rmtree(state["dir"], ignore_errors=True)

    print(f"转换完成，结果保存到: {output_path}")
    return output_path


def batch_convert_pdf_to_word(
    input_dir,
    output_dir=None,
    include_images=True,
    start_page=None,
    end_page=None,
):
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    if output_dir is None:
        output_dir = input_dir

    pdf_files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("未找到PDF文件")
        return []

    print(f"找到 {len(pdf_files)} 个PDF文件")

    all_results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        print(f"\n处理文件: {pdf_file}")
        try:
            pdf_name = os.path.splitext(pdf_file)[0]
            output_path = os.path.join(output_dir, f"{pdf_name}.docx")
            result = convert_pdf_to_word(
                pdf_path,
                output_path=output_path,
                include_images=include_images,
                start_page=start_page,
                end_page=end_page,
            )
            all_results.append(result)
        except Exception as e:
            print(f"处理 {pdf_file} 失败: {e}")

    return all_results


def batch_convert_pdf_to_excel(
    input_dir,
    output_dir=None,
    table_only=False,
    start_page=None,
    end_page=None,
):
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    if output_dir is None:
        output_dir = input_dir

    pdf_files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("未找到PDF文件")
        return []

    print(f"找到 {len(pdf_files)} 个PDF文件")

    all_results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        print(f"\n处理文件: {pdf_file}")
        try:
            pdf_name = os.path.splitext(pdf_file)[0]
            output_path = os.path.join(output_dir, f"{pdf_name}.xlsx")
            result = convert_pdf_to_excel(
                pdf_path,
                output_path=output_path,
                table_only=table_only,
                start_page=start_page,
                end_page=end_page,
            )
            all_results.append(result)
        except Exception as e:
            print(f"处理 {pdf_file} 失败: {e}")

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF转Office工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    word_parser = subparsers.add_parser("word", help="PDF转Word")
    word_parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    word_parser.add_argument("-o", "--output", help="输出目录")
    word_parser.add_argument("-i", "--include-images", action="store_true", help="包含图片")
    word_parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    word_parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")

    excel_parser = subparsers.add_parser("excel", help="PDF转Excel")
    excel_parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    excel_parser.add_argument("-o", "--output", help="输出目录")
    excel_parser.add_argument("-t", "--table-only", action="store_true", help="仅提取表格")
    excel_parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    excel_parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")

    args = parser.parse_args()

    if args.command == "word":
        if os.path.isfile(args.pdf_path):
            convert_pdf_to_word(
                args.pdf_path,
                output_path=args.output,
                include_images=args.include_images,
                start_page=args.start_page,
                end_page=args.end_page,
            )
        elif os.path.isdir(args.pdf_path):
            batch_convert_pdf_to_word(
                args.pdf_path,
                output_dir=args.output,
                include_images=args.include_images,
                start_page=args.start_page,
                end_page=args.end_page,
            )
        else:
            print(f"路径不存在: {args.pdf_path}")
    elif args.command == "excel":
        if os.path.isfile(args.pdf_path):
            convert_pdf_to_excel(
                args.pdf_path,
                output_path=args.output,
                table_only=args.table_only,
                start_page=args.start_page,
                end_page=args.end_page,
            )
        elif os.path.isdir(args.pdf_path):
            batch_convert_pdf_to_excel(
                args.pdf_path,
                output_dir=args.output,
                table_only=args.table_only,
                start_page=args.start_page,
                end_page=args.end_page,
            )
        else:
            print(f"路径不存在: {args.pdf_path}")
    else:
        parser.print_help()