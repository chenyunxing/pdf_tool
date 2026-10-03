import os
import shutil
from pdf2image import convert_from_path
from .poppler import get_poppler_path


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


def convert_pdf_to_images(
    pdf_path,
    output_dir=None,
    image_format="png",
    dpi=200,
    start_page=None,
    end_page=None,
    clear_existing=True
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_dir is None:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(pdf_dir, "images", pdf_name)

    os.makedirs(output_dir, exist_ok=True)

    if clear_existing:
        clear_folder(output_dir)

    image_format = image_format.lower()
    valid_formats = ["png", "jpg", "jpeg", "ppm", "tif", "tiff"]
    if image_format not in valid_formats:
        raise ValueError(f"不支持的图片格式: {image_format}，支持的格式: {', '.join(valid_formats)}")

    print(f"开始将PDF转换为{image_format.upper()}图片...")

    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=start_page,
        last_page=end_page,
        poppler_path=get_poppler_path(),
    )

    total_pages = len(images)
    print(f"PDF共 {total_pages} 页")

    saved_paths = []
    for i, image in enumerate(images):
        page_num = i + 1 if start_page is None else start_page + i
        image_path = os.path.join(output_dir, f"page_{page_num}.{image_format}")
        image.save(image_path)
        saved_paths.append(image_path)

        if i % 10 == 0:
            print(f"已保存 {i+1} 张图片")

    print(f"转换完成，共保存 {len(saved_paths)} 张图片到: {output_dir}")
    return saved_paths


def batch_convert_pdf_to_images(
    input_dir,
    output_dir=None,
    image_format="png",
    dpi=200,
    start_page=None,
    end_page=None,
    clear_existing=True
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
            file_output_dir = os.path.join(output_dir, "images", pdf_name)
            results = convert_pdf_to_images(
                pdf_path,
                output_dir=file_output_dir,
                image_format=image_format,
                dpi=dpi,
                start_page=start_page,
                end_page=end_page,
                clear_existing=clear_existing
            )
            all_results.extend(results)
        except Exception as e:
            print(f"处理 {pdf_file} 失败: {e}")

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF转图片工具")
    parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("-f", "--format", default="png", help="输出图片格式（png/jpg/jpeg/ppm/tif/tiff）")
    parser.add_argument("-d", "--dpi", type=int, default=200, help="图片分辨率（DPI）")
    parser.add_argument("-s", "--start-page", type=int, help="起始页码（从1开始）")
    parser.add_argument("-e", "--end-page", type=int, help="结束页码（从1开始）")
    parser.add_argument("-k", "--keep-existing", action="store_true", help="保留输出目录中已存在的文件")

    args = parser.parse_args()

    clear_existing = not args.keep_existing

    if os.path.isfile(args.pdf_path):
        convert_pdf_to_images(
            args.pdf_path,
            output_dir=args.output,
            image_format=args.format,
            dpi=args.dpi,
            start_page=args.start_page,
            end_page=args.end_page,
            clear_existing=clear_existing
        )
    elif os.path.isdir(args.pdf_path):
        batch_convert_pdf_to_images(
            args.pdf_path,
            output_dir=args.output,
            image_format=args.format,
            dpi=args.dpi,
            start_page=args.start_page,
            end_page=args.end_page,
            clear_existing=clear_existing
        )
    else:
        print(f"路径不存在: {args.pdf_path}")