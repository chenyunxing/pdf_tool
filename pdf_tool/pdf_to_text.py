import os
import shutil
from pdf2image import convert_from_path
from .wechat_ocr import WeChatOCR


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


def convert_pdf_to_text(
    pdf_path,
    output_dir=None,
    image_dir=None,
    skip_pages=None,
    min_text_length=50,
    wechat_path=None,
    wechatocr_path=None
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_dir is None:
        output_dir = os.path.dirname(pdf_path)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    if image_dir is None:
        image_dir = os.path.join(output_dir, "images", pdf_name)

    if skip_pages is None:
        skip_pages = []

    os.makedirs(image_dir, exist_ok=True)
    clear_folder(image_dir)

    print("开始将PDF转换为图片...")
    images = convert_from_path(pdf_path)
    print(f"PDF共 {len(images)} 页")

    for i, image in enumerate(images):
        image_path = os.path.join(image_dir, f"page_{i+1}.png")
        image.save(image_path)
        if i % 10 == 0:
            print(f"已保存 {i+1} 张图片")

    print("开始OCR识别...")
    full_text = ""

    ocr = WeChatOCR(wechat_path, wechatocr_path)

    try:
        for i in range(len(images)):
            if i in skip_pages:
                continue

            image_path = os.path.join(image_dir, f"page_{i+1}.png")

            try:
                result = ocr.ocr(image_path)
                page_text = ""
                for item in result.get('ocr_response', []):
                    page_text += "\n" + item.get('text', '')
                page_text = page_text.strip()

                if len(page_text) > min_text_length:
                    full_text += "\n" + page_text

                if i % 10 == 0:
                    print(f"已识别 {i+1} 页")

            except Exception as e:
                print(f"第 {i+1} 页识别失败: {e}")
                continue
    finally:
        ocr.stop()

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(output_dir, f"{pdf_name}.txt")

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"文本已保存到: {txt_path}")
    return txt_path


def convert_pdf_to_text_with_ocr(
    pdf_path,
    ocr,
    output_dir=None,
    image_dir=None,
    skip_pages=None,
    min_text_length=50
):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    if output_dir is None:
        output_dir = os.path.dirname(pdf_path)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    if image_dir is None:
        image_dir = os.path.join(output_dir, "images", pdf_name)

    if skip_pages is None:
        skip_pages = []

    os.makedirs(image_dir, exist_ok=True)
    clear_folder(image_dir)

    print("开始将PDF转换为图片...")
    images = convert_from_path(pdf_path)
    print(f"PDF共 {len(images)} 页")

    for i, image in enumerate(images):
        image_path = os.path.join(image_dir, f"page_{i+1}.png")
        image.save(image_path)
        if i % 10 == 0:
            print(f"已保存 {i+1} 张图片")

    print("开始OCR识别...")
    full_text = ""

    for i in range(len(images)):
        if i in skip_pages:
            continue

        image_path = os.path.join(image_dir, f"page_{i+1}.png")

        try:
            result = ocr.ocr(image_path)
            page_text = ""
            for item in result.get('ocr_response', []):
                page_text += "\n" + item.get('text', '')
            page_text = page_text.strip()

            if len(page_text) > min_text_length:
                full_text += "\n" + page_text

            if i % 10 == 0:
                print(f"已识别 {i+1} 页")

        except Exception as e:
            print(f"第 {i+1} 页识别失败: {e}")
            continue

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(output_dir, f"{pdf_name}.txt")

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    print(f"文本已保存到: {txt_path}")
    return txt_path


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