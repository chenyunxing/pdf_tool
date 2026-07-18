import os
from PyPDF2 import PdfReader, PdfWriter


def split_pdf(
    pdf_path,
    output_dir=None,
    pages_per_file=1,
    start_page=None,
    end_page=None
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_dir is None:
        output_dir = os.path.dirname(pdf_path)

    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    if start_page is None:
        start_page = 0
    else:
        start_page = max(0, start_page - 1)

    if end_page is None:
        end_page = total_pages
    else:
        end_page = min(total_pages, end_page)

    if start_page >= end_page:
        raise ValueError("起始页码必须小于结束页码")

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    results = []

    for i in range(start_page, end_page, pages_per_file):
        writer = PdfWriter()
        end = min(i + pages_per_file, end_page)

        for j in range(i, end):
            writer.add_page(reader.pages[j])

        output_filename = f"{pdf_name}_pages_{i+1}-{end}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "wb") as f:
            writer.write(f)

        results.append(output_path)
        print(f"已生成: {output_path}")

    print(f"拆分完成，共生成 {len(results)} 个文件")
    return results


def merge_pdfs(
    pdf_paths,
    output_path=None
):
    if not pdf_paths:
        raise ValueError("PDF文件列表不能为空")

    for pdf_path in pdf_paths:
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_path is None:
        output_dir = os.path.dirname(pdf_paths[0])
        output_path = os.path.join(output_dir, "merged_output.pdf")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    writer = PdfWriter()

    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
        print(f"已添加: {pdf_path}")

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"合并完成，结果保存到: {output_path}")
    return output_path


def delete_pages(
    pdf_path,
    pages_to_delete,
    output_path=None
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if not pages_to_delete:
        raise ValueError("要删除的页码列表不能为空")

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    pages_to_delete = sorted(set(pages_to_delete))

    for page in pages_to_delete:
        if page < 1 or page > total_pages:
            raise ValueError(f"页码 {page} 超出范围（PDF共 {total_pages} 页）")

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}_deleted.pdf")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    writer = PdfWriter()

    for i in range(total_pages):
        if (i + 1) not in pages_to_delete:
            writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"已删除页码: {', '.join(map(str, pages_to_delete))}")
    print(f"删除完成，结果保存到: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF拆分、合并和删除工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    split_parser = subparsers.add_parser("split", help="拆分PDF")
    split_parser.add_argument("pdf_path", help="要拆分的PDF文件路径")
    split_parser.add_argument("-o", "--output", help="输出目录")
    split_parser.add_argument("-p", "--pages-per-file", type=int, default=1, help="每个输出文件的页数")
    split_parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    split_parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")

    merge_parser = subparsers.add_parser("merge", help="合并PDF")
    merge_parser.add_argument("pdf_paths", nargs="+", help="要合并的PDF文件路径列表")
    merge_parser.add_argument("-o", "--output", help="输出文件路径")

    delete_parser = subparsers.add_parser("delete", help="删除PDF指定页码")
    delete_parser.add_argument("pdf_path", help="要处理的PDF文件路径")
    delete_parser.add_argument("pages", type=int, nargs="+", help="要删除的页码（从1开始）")
    delete_parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()

    if args.command == "split":
        split_pdf(
            args.pdf_path,
            output_dir=args.output,
            pages_per_file=args.pages_per_file,
            start_page=args.start_page,
            end_page=args.end_page
        )
    elif args.command == "merge":
        merge_pdfs(
            args.pdf_paths,
            output_path=args.output
        )
    elif args.command == "delete":
        delete_pages(
            args.pdf_path,
            pages_to_delete=args.pages,
            output_path=args.output
        )
    else:
        parser.print_help()