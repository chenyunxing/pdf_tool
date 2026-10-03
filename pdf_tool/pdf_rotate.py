import os

ANGLES = (90, 180, 270)


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


def _output_path(pdf_path: str, output_path: str | None, suffix: str) -> str:
    if output_path is None:
        directory = os.path.dirname(pdf_path)
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(directory, f"{name}{suffix}.pdf")
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return output_path


def rotate_pdf(
    pdf_path: str,
    angle: int = 90,
    output_path: str | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> str:
    import fitz

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    if angle not in ANGLES:
        raise ValueError("角度只接受 90、180 或 270")

    output_path = _output_path(pdf_path, output_path, "_rotated")
    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    try:
        first, last = _page_bounds(doc.page_count, start_page, end_page)
        for index in range(first - 1, last):
            page = doc[index]
            page.set_rotation((page.rotation + angle) % 360)
        doc.save(output_path)
    finally:
        doc.close()

    print(f"旋转完成，结果保存到: {output_path}")
    return output_path


def batch_rotate_pdf(
    input_dir,
    output_dir=None,
    angle=90,
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
        target = os.path.join(output_dir, f"{name}_rotated.pdf")
        try:
            results.append(
                rotate_pdf(
                    pdf_path,
                    angle=angle,
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

    parser = argparse.ArgumentParser(description="PDF旋转工具")
    parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    parser.add_argument("-o", "--output", help="输出文件路径或目录")
    parser.add_argument("-a", "--angle", type=int, default=90, choices=ANGLES, help="顺时针角度：90、180 或 270")
    parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")
    args = parser.parse_args()

    if os.path.isfile(args.pdf_path):
        rotate_pdf(
            args.pdf_path,
            angle=args.angle,
            output_path=args.output,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    elif os.path.isdir(args.pdf_path):
        batch_rotate_pdf(
            args.pdf_path,
            output_dir=args.output,
            angle=args.angle,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    else:
        print(f"路径不存在: {args.pdf_path}")
