import os
import shutil
import struct
import subprocess
from pdf2image import pdfinfo_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
from .poppler import get_poppler_path
from .wechat_ocr import WeChatOCR

DEFAULT_RENDER_DPI = 200


class ConversionStopped(Exception):
    pass


def clear_folder(folder_path):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")


def _page_count(pdf_path, poppler_path):
    try:
        info = pdfinfo_from_path(os.path.abspath(pdf_path), poppler_path=poppler_path)
    except (PDFInfoNotInstalledError, PDFPageCountError) as e:
        raise RuntimeError(f"读取PDF页数失败: {pdf_path}: {e}") from e
    return int(info["Pages"])


def _render_page(pdf_path, page_number, image_path, poppler_path, dpi):
    prefix = os.path.splitext(image_path)[0]
    command = [
        os.path.join(poppler_path, "pdftoppm.exe"),
        "-r", str(dpi),
        "-f", str(page_number),
        "-l", str(page_number),
        "-png",
        "-singlefile",
        os.path.abspath(pdf_path),
        prefix,
    ]
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
    )
    if result.returncode != 0 or not os.path.isfile(image_path):
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"第 {page_number} 页转图片失败: {pdf_path}: {err}")


def _png_width(image_path: str, page_number: int) -> int:
    with open(image_path, "rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"第 {page_number} 页图片无效: {image_path}")
    return struct.unpack(">I", header[16:20])[0]


def recognize_pdf_page(pdf_path: str, page_number: int, ocr, image_dir: str) -> tuple[list[dict], int]:
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, f"page_{page_number}.png")
    try:
        _render_page(pdf_path, page_number, image_path, get_poppler_path(), DEFAULT_RENDER_DPI)
        width = _png_width(image_path, page_number)
        result = ocr.ocr(image_path)
        return list(result.get("ocr_response") or []), width
    finally:
        _delete_file(image_path)


def _extract_page_text(ocr, image_path):
    result = ocr.ocr(image_path)
    page_text = ""
    for item in result.get("ocr_response", []):
        page_text += "\n" + item.get("text", "")
    return page_text.strip()


def _delete_file(file_path):
    if not os.path.isfile(file_path):
        return
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"删除文件失败 {file_path}: {e}")


def _cleanup_image_dir(image_dir, remove_empty_parent):
    if not os.path.isdir(image_dir):
        return

    for filename in os.listdir(image_dir):
        file_path = os.path.join(image_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as e:
            print(f"删除文件失败 {file_path}: {e}")

    if os.listdir(image_dir):
        return

    try:
        os.rmdir(image_dir)
    except OSError as e:
        print(f"删除文件失败 {image_dir}: {e}")
        return

    if not remove_empty_parent:
        return

    parent = os.path.dirname(image_dir)
    if os.path.basename(parent) != "images" or not os.path.isdir(parent) or os.listdir(parent):
        return
    try:
        os.rmdir(parent)
    except OSError as e:
        print(f"删除文件失败 {parent}: {e}")


def _append_page_text(txt_file, page_text):
    txt_file.write("\n" + page_text)
    txt_file.flush()


def _recognize_pdf(
    pdf_path,
    ocr,
    image_dir,
    skip_pages,
    min_text_length,
    txt_file,
    poppler_path,
    page_count,
    on_page=None,
    on_page_error=None,
    should_continue=None,
):
    print(f"PDF共 {page_count} 页，开始逐页识别...")

    skipped = set(skip_pages)
    for index in range(page_count):
        if should_continue is not None and not should_continue():
            raise ConversionStopped()
        if index in skipped:
            continue

        page_number = index + 1
        if on_page is not None:
            on_page(page_number, page_count)
        image_path = os.path.join(image_dir, f"page_{page_number}.png")
        try:
            _render_page(pdf_path, page_number, image_path, poppler_path, DEFAULT_RENDER_DPI)
            page_text = _extract_page_text(ocr, image_path)
            if len(page_text) > min_text_length:
                _append_page_text(txt_file, page_text)
            if index % 10 == 0:
                print(f"已识别 {page_number} 页")
        except Exception as e:
            print(f"第 {page_number} 页识别失败: {e}")
            if on_page_error is not None:
                on_page_error(page_number, str(e))
        finally:
            _delete_file(image_path)


def _convert_pdf_to_text(
    pdf_path,
    ocr,
    output_dir,
    image_dir,
    skip_pages,
    min_text_length,
    on_page=None,
    on_page_error=None,
    should_continue=None,
):
    if output_dir is None:
        output_dir = os.path.dirname(pdf_path) or "."

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    remove_empty_parent = image_dir is None
    if image_dir is None:
        image_dir = os.path.join(output_dir, "images", pdf_name)

    if skip_pages is None:
        skip_pages = []

    txt_path = os.path.join(output_dir, f"{pdf_name}.txt")
    poppler_path = get_poppler_path()
    page_count = _page_count(pdf_path, poppler_path)
    os.makedirs(image_dir, exist_ok=True)
    clear_folder(image_dir)
    print(f"文本写入: {txt_path}")
    with open(txt_path, "w", encoding="utf-8") as txt_file:
        try:
            _recognize_pdf(
                pdf_path,
                ocr,
                image_dir,
                skip_pages,
                min_text_length,
                txt_file,
                poppler_path,
                page_count,
                on_page=on_page,
                on_page_error=on_page_error,
                should_continue=should_continue,
            )
        finally:
            _cleanup_image_dir(image_dir, remove_empty_parent)

    print(f"文本已保存到: {txt_path}")
    return txt_path


def pdf_page_count(pdf_path: str) -> int:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    return _page_count(pdf_path, get_poppler_path())


def convert_pdf_to_text(
    pdf_path,
    output_dir=None,
    image_dir=None,
    skip_pages=None,
    min_text_length=50,
    wechat_path=None,
    wechatocr_path=None,
    on_page=None,
    on_page_error=None,
    should_continue=None,
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    ocr = WeChatOCR(wechat_path, wechatocr_path)
    try:
        return _convert_pdf_to_text(
            pdf_path,
            ocr,
            output_dir,
            image_dir,
            skip_pages,
            min_text_length,
            on_page=on_page,
            on_page_error=on_page_error,
            should_continue=should_continue,
        )
    finally:
        ocr.stop()


def convert_pdf_to_text_with_ocr(
    pdf_path,
    ocr,
    output_dir=None,
    image_dir=None,
    skip_pages=None,
    min_text_length=50,
    on_page=None,
    on_page_error=None,
    should_continue=None,
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    return _convert_pdf_to_text(
        pdf_path,
        ocr,
        output_dir,
        image_dir,
        skip_pages,
        min_text_length,
        on_page=on_page,
        on_page_error=on_page_error,
        should_continue=should_continue,
    )


def batch_convert_pdf_to_text(
    input_dir,
    output_dir=None,
    image_dir=None,
    skip_pages=None,
    min_text_length=50,
    wechat_path=None,
    wechatocr_path=None
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

    ocr = WeChatOCR(wechat_path, wechatocr_path)

    results = []
    try:
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_dir, pdf_file)
            print(f"\n处理文件: {pdf_file}")
            try:
                txt_path = convert_pdf_to_text_with_ocr(
                    pdf_path,
                    ocr,
                    output_dir=output_dir,
                    image_dir=image_dir,
                    skip_pages=skip_pages,
                    min_text_length=min_text_length
                )
                results.append(txt_path)
            except Exception as e:
                print(f"处理 {pdf_file} 失败: {e}")
    finally:
        ocr.stop()

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF转文本工具")
    parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("-i", "--image-dir", help="临时图片目录")
    parser.add_argument("-s", "--skip", type=int, nargs="+", help="需要跳过的页码（从1开始）")
    parser.add_argument("-m", "--min-length", type=int, default=50, help="最小文本长度")
    parser.add_argument("-w", "--wechat-path", help="微信资源路径")
    parser.add_argument("-c", "--ocr-path", help="WeChatOCR.exe路径")

    args = parser.parse_args()

    skip_pages = [p - 1 for p in args.skip] if args.skip else None

    if os.path.isfile(args.pdf_path):
        convert_pdf_to_text(
            args.pdf_path,
            output_dir=args.output,
            image_dir=args.image_dir,
            skip_pages=skip_pages,
            min_text_length=args.min_length,
            wechat_path=args.wechat_path,
            wechatocr_path=args.ocr_path
        )
    elif os.path.isdir(args.pdf_path):
        batch_convert_pdf_to_text(
            args.pdf_path,
            output_dir=args.output,
            image_dir=args.image_dir,
            skip_pages=skip_pages,
            min_text_length=args.min_length,
            wechat_path=args.wechat_path,
            wechatocr_path=args.ocr_path
        )
    else:
        print(f"路径不存在: {args.pdf_path}")
