import os


def convert_pdf_to_word(
    pdf_path,
    output_path=None,
    include_images=True
):
    import fitz
    from docx import Document
    from docx.shared import Inches

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    word_doc = Document()

    print("提取文本和图片...")
    for page_num in range(len(doc)):
        page = doc[page_num]

        text = page.get_text()
        if text.strip():
            word_doc.add_paragraph(text)

        if include_images:
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                try:
                    import io
                    image_stream = io.BytesIO(image_bytes)
                    word_doc.add_picture(image_stream, width=Inches(5))
                except Exception as e:
                    print(f"添加图片失败: {e}")

        if page_num < len(doc) - 1:
            word_doc.add_page_break()

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}.docx")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    word_doc.save(output_path)
    doc.close()

    print(f"转换完成，结果保存到: {output_path}")
    return output_path


def convert_pdf_to_excel(
    pdf_path,
    output_path=None,
    table_only=False
):
    import fitz
    from openpyxl import Workbook

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    wb = Workbook()
    ws = wb.active
    ws.title = "PDF内容"

    print("提取表格数据...")
    row_idx = 1

    for page_num in range(len(doc)):
        page = doc[page_num]

        tables = page.find_tables()
        for table in tables:
            for i, row in enumerate(table.extract()):
                for j, cell in enumerate(row):
                    ws.cell(row=row_idx, column=j + 1, value=cell)
                row_idx += 1
            row_idx += 1

        if not table_only:
            text = page.get_text()
            if text.strip():
                ws.cell(row=row_idx, column=1, value=f"--- 第 {page_num + 1} 页 ---")
                row_idx += 1
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        ws.cell(row=row_idx, column=1, value=line.strip())
                        row_idx += 1

        row_idx += 2

    if output_path is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(pdf_dir, f"{pdf_name}.xlsx")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    wb.save(output_path)
    doc.close()

    print(f"转换完成，结果保存到: {output_path}")
    return output_path


def batch_convert_pdf_to_word(
    input_dir,
    output_dir=None,
    include_images=True
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
                include_images=include_images
            )
            all_results.append(result)
        except Exception as e:
            print(f"处理 {pdf_file} 失败: {e}")

    return all_results


def batch_convert_pdf_to_excel(
    input_dir,
    output_dir=None,
    table_only=False
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
                table_only=table_only
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

    excel_parser = subparsers.add_parser("excel", help="PDF转Excel")
    excel_parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    excel_parser.add_argument("-o", "--output", help="输出目录")
    excel_parser.add_argument("-t", "--table-only", action="store_true", help="仅提取表格")

    args = parser.parse_args()

    if args.command == "word":
        if os.path.isfile(args.pdf_path):
            convert_pdf_to_word(
                args.pdf_path,
                output_path=args.output,
                include_images=args.include_images
            )
        elif os.path.isdir(args.pdf_path):
            batch_convert_pdf_to_word(
                args.pdf_path,
                output_dir=args.output,
                include_images=args.include_images
            )
        else:
            print(f"路径不存在: {args.pdf_path}")
    elif args.command == "excel":
        if os.path.isfile(args.pdf_path):
            convert_pdf_to_excel(
                args.pdf_path,
                output_path=args.output,
                table_only=args.table_only
            )
        elif os.path.isdir(args.pdf_path):
            batch_convert_pdf_to_excel(
                args.pdf_path,
                output_dir=args.output,
                table_only=args.table_only
            )
        else:
            print(f"路径不存在: {args.pdf_path}")
    else:
        parser.print_help()