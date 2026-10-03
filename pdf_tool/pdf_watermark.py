import os

FONT_CANDIDATES = (
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\arial.ttf",
)
MAX_TEXT_LENGTH = 80


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


def _output_path(pdf_path: str, output_path: str | None) -> str:
    if output_path is None:
        directory = os.path.dirname(pdf_path)
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(directory, f"{name}_watermarked.pdf")
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return output_path


def _load_font(fitz):
    for path in FONT_CANDIDATES:
        if not os.path.isfile(path):
            continue
        try:
            return fitz.Font(fontfile=path)
        except (ValueError, RuntimeError):
            continue
    raise FileNotFoundError("找不到可用的水印字体")


def _stamp(page, text: str, font) -> None:
    import fitz

    rect = page.rect
    limit = min(rect.width, rect.height) * 0.62
    fontsize = 54
    length = font.text_length(text, fontsize)
    if length > limit and length > 0:
        fontsize = max(16, fontsize * limit / length)
        length = font.text_length(text, fontsize)
    origin = fitz.Point((rect.width - length) / 2, rect.height / 2 + fontsize * 0.35)
    writer = fitz.TextWriter(rect, color=(0.45, 0.45, 0.45), opacity=0.28)
    writer.append(origin, text, font=font, fontsize=fontsize)
    center = fitz.Point(rect.width / 2, rect.height / 2)
    writer.write_text(page, overlay=True, morph=(center, fitz.Matrix(45)))


def add_watermark(
    pdf_path: str,
    text: str,
    output_path: str | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    import fitz

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("请填写水印文字")
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError("水印文字不能超过 80 个字")

    output_path = _output_path(pdf_path, output_path)
    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ValueError(f"这份 PDF 已加密，不能加水印: {pdf_path}")
        first, last = _page_bounds(doc.page_count, start_page, end_page)
        font = _load_font(fitz)
        for index in range(first - 1, last):
            _stamp(doc[index], text, font)
        doc.save(output_path)
    finally:
        doc.close()

    print(f"水印完成，结果保存到: {output_path}")
    return output_path


def batch_add_watermark(
    input_dir,
    text,
    output_dir=None,
    start_page=None,
    end_page=None,
):
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    if output_dir is None:
        output_dir = input_dir

    pdf_files = [name for name in os.listdir(input_dir) if name.lower().endswith(".pdf")]
    if not pdf_files:
        print("未找到PDF文件")
        return []

    results = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        name = os.path.splitext(pdf_file)[0]
        target = os.path.join(output_dir, f"{name}_watermarked.pdf")
        try:
            results.append(
                add_watermark(
                    pdf_path,
                    text,
                    output_path=target,
                    start_page=start_page,
                    end_page=end_page,
                )
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"处理 {pdf_file} 失败: {exc}")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF水印工具")
    parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    parser.add_argument("-t", "--text", required=True, help="水印文字")
    parser.add_argument("-o", "--output", help="输出文件路径或目录")
    parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")
    args = parser.parse_args()

    if os.path.isfile(args.pdf_path):
        add_watermark(
            args.pdf_path,
            args.text,
            output_path=args.output,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    elif os.path.isdir(args.pdf_path):
        batch_add_watermark(
            args.pdf_path,
            args.text,
            output_dir=args.output,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    else:
        print(f"路径不存在: {args.pdf_path}")
