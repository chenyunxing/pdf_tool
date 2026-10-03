import io
import os


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


def compress_pdf(
    pdf_path: str,
    output_path: str | None = None,
    compression_level: int = 3,
    start_page: int | None = None,
    end_page: int | None = None,
) -> dict:
    import fitz

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if compression_level < 1 or compression_level > 5:
        raise ValueError("压缩级别必须在1-5之间")

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}_compressed.pdf")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    subset = None
    try:
        first, last = _page_bounds(doc.page_count, start_page, end_page)
        working = doc
        original_size = os.path.getsize(pdf_path)
        if first != 1 or last != doc.page_count:
            subset = fitz.open()
            subset.insert_pdf(doc, from_page=first - 1, to_page=last - 1)
            working = subset
            buffer = io.BytesIO()
            working.save(buffer, garbage=0, deflate=False)
            original_size = buffer.tell()

        if compression_level >= 3:
            print("优化图片...")
            for page in working:
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = working.extract_image(xref)
                    image_bytes = base_image["image"]

                    if compression_level >= 4:
                        try:
                            pix = fitz.Pixmap(base_image)
                            if pix.n > 4:
                                pix = fitz.Pixmap(fitz.csRGB, pix)

                            if compression_level == 5:
                                pix.set_dpi(pix.xres // 2, pix.yres // 2)

                            new_image = pix.tobytes("png")
                            if len(new_image) < len(image_bytes):
                                working.update_image(xref, new_image)
                            pix = None
                        except (ValueError, RuntimeError):
                            pass

        print("保存压缩后的PDF...")
        working.save(output_path, garbage=compression_level, deflate=True)
    finally:
        if subset is not None:
            subset.close()
        doc.close()

    compressed_size = os.path.getsize(output_path)
    compression_ratio = (1 - compressed_size / original_size) * 100

    print(f"压缩完成，结果保存到: {output_path}")
    print(f"原始大小: {original_size / 1024:.2f} KB")
    print(f"压缩后大小: {compressed_size / 1024:.2f} KB")
    print(f"压缩率: {compression_ratio:.2f}%")

    return {
        'output_path': output_path,
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': compression_ratio
    }


def batch_compress_pdf(
    input_dir,
    output_dir=None,
    compression_level=3,
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
            output_path = os.path.join(output_dir, f"{pdf_name}_compressed.pdf")
            result = compress_pdf(
                pdf_path,
                output_path=output_path,
                compression_level=compression_level,
                start_page=start_page,
                end_page=end_page,
            )
            all_results.append(result)
        except Exception as e:
            print(f"处理 {pdf_file} 失败: {e}")

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF压缩工具")
    parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    parser.add_argument("-o", "--output", help="输出目录或文件路径")
    parser.add_argument(
        "-c",
        "--compression-level",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="压缩级别（1-5，级别越高压缩率越大）"
    )
    parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")

    args = parser.parse_args()

    if os.path.isfile(args.pdf_path):
        compress_pdf(
            args.pdf_path,
            output_path=args.output,
            compression_level=args.compression_level,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    elif os.path.isdir(args.pdf_path):
        batch_compress_pdf(
            args.pdf_path,
            output_dir=args.output,
            compression_level=args.compression_level,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    else:
        print(f"路径不存在: {args.pdf_path}")