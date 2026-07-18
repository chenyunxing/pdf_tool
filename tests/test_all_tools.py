import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_tool.pdf_split_merge import split_pdf, merge_pdfs, delete_pages
from pdf_tool.pdf_to_image import convert_pdf_to_images
from pdf_tool.pdf_compress import compress_pdf
from pdf_tool.pdf_to_office import convert_pdf_to_word, convert_pdf_to_excel
from pdf_tool.pdf_to_text import convert_pdf_to_text


def create_test_pdfs(test_dir):
    pdf_files = [f for f in os.listdir(test_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("未找到PDF文件")
        return []

    test_pdfs_dir = os.path.join(test_dir, "test_pdfs")
    os.makedirs(test_pdfs_dir, exist_ok=True)

    for pdf_file in pdf_files:
        pdf_path = os.path.join(test_dir, pdf_file)
        pdf_name = os.path.splitext(pdf_file)[0]

        try:
            split_pdf(pdf_path, output_dir=test_pdfs_dir, pages_per_file=7)
            print(f"已将 {pdf_file} 分割为7页的小PDF")
        except Exception as e:
            print(f"分割 {pdf_file} 失败: {e}")

    small_pdfs = [os.path.join(test_pdfs_dir, f) for f in os.listdir(test_pdfs_dir) if f.lower().endswith(".pdf")]
    return small_pdfs


def test_split_pdf(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF拆分功能")
    print("=" * 60)

    output_dir = os.path.join(test_dir, "output", "split")
    os.makedirs(output_dir, exist_ok=True)

    try:
        results = split_pdf(test_pdf, output_dir=output_dir, pages_per_file=2)
        print(f"拆分完成，生成 {len(results)} 个文件")
        for r in results:
            print(f"  - {os.path.basename(r)}")
        return True
    except Exception as e:
        print(f"拆分失败: {e}")
        return False


def test_merge_pdfs(test_dir, test_pdfs):
    print("\n" + "=" * 60)
    print("测试: PDF合并功能")
    print("=" * 60)

    output_path = os.path.join(test_dir, "output", "merged_output.pdf")

    try:
        result = merge_pdfs(test_pdfs[:3], output_path=output_path)
        print(f"合并完成，结果保存到: {os.path.basename(result)}")
        return True
    except Exception as e:
        print(f"合并失败: {e}")
        return False


def test_delete_pages(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF删除页面功能")
    print("=" * 60)

    output_path = os.path.join(test_dir, "output", "deleted_output.pdf")

    try:
        result = delete_pages(test_pdf, pages_to_delete=[1, 2], output_path=output_path)
        print(f"删除完成，结果保存到: {os.path.basename(result)}")
        return True
    except Exception as e:
        print(f"删除失败: {e}")
        return False


def test_pdf_to_images(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF转图片功能")
    print("=" * 60)

    output_dir = os.path.join(test_dir, "output", "images")
    os.makedirs(output_dir, exist_ok=True)

    try:
        results = convert_pdf_to_images(test_pdf, output_dir=output_dir, image_format="png", dpi=150)
        print(f"转换完成，生成 {len(results)} 张图片")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def test_pdf_compress(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF压缩功能")
    print("=" * 60)

    output_path = os.path.join(test_dir, "output", "compressed_output.pdf")

    try:
        result = compress_pdf(test_pdf, output_path=output_path, compression_level=3)
        print(f"压缩完成，结果保存到: {os.path.basename(result['output_path'])}")
        print(f"原始大小: {result['original_size'] / 1024:.2f} KB")
        print(f"压缩后大小: {result['compressed_size'] / 1024:.2f} KB")
        print(f"压缩率: {result['compression_ratio']:.2f}%")
        return True
    except Exception as e:
        print(f"压缩失败: {e}")
        return False


def test_pdf_to_word(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF转Word功能")
    print("=" * 60)

    output_path = os.path.join(test_dir, "output", "output.docx")

    try:
        result = convert_pdf_to_word(test_pdf, output_path=output_path, include_images=True)
        print(f"转换完成，结果保存到: {os.path.basename(result)}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def test_pdf_to_excel(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF转Excel功能")
    print("=" * 60)

    output_path = os.path.join(test_dir, "output", "output.xlsx")

    try:
        result = convert_pdf_to_excel(test_pdf, output_path=output_path, table_only=False)
        print(f"转换完成，结果保存到: {os.path.basename(result)}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def test_pdf_to_text(test_dir, test_pdf):
    print("\n" + "=" * 60)
    print("测试: PDF转文本功能")
    print("=" * 60)

    output_dir = os.path.join(test_dir, "output")

    try:
        result = convert_pdf_to_text(test_pdf, output_dir=output_dir)
        print(f"转换完成，结果保存到: {os.path.basename(result)}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(test_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("PDF工具包 - 全功能测试脚本")
    print("=" * 60)
    print(f"测试目录: {test_dir}")
    print(f"输出目录: {output_dir}")

    print("\n" + "=" * 60)
    print("步骤1: 将测试PDF分割为小文件（每7页）")
    print("=" * 60)
    test_pdfs = create_test_pdfs(test_dir)

    if not test_pdfs:
        print("未找到可测试的PDF文件")
        return

    print(f"\n找到 {len(test_pdfs)} 个测试PDF文件")
    for pdf in test_pdfs:
        print(f"  - {os.path.basename(pdf)}")

    test_pdf = test_pdfs[0]
    print(f"\n使用测试文件: {os.path.basename(test_pdf)}")

    results = []

    results.append(("PDF拆分", test_split_pdf(test_dir, test_pdf)))
    results.append(("PDF合并", test_merge_pdfs(test_dir, test_pdfs)))
    results.append(("PDF删除页面", test_delete_pages(test_dir, test_pdf)))
    results.append(("PDF转图片", test_pdf_to_images(test_dir, test_pdf)))
    results.append(("PDF压缩", test_pdf_compress(test_dir, test_pdf)))
    results.append(("PDF转Word", test_pdf_to_word(test_dir, test_pdf)))
    results.append(("PDF转Excel", test_pdf_to_excel(test_dir, test_pdf)))
    results.append(("PDF转文本", test_pdf_to_text(test_dir, test_pdf)))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")

    print("\n" + "=" * 60)
    print(f"测试完成: {passed}/{total} 通过")
    print("=" * 60)

    if passed < total:
        print("\n部分测试失败，请检查错误信息并修复问题。")
    else:
        print("\n所有测试通过！请检查 output 目录中的测试结果文件。")


if __name__ == "__main__":
    main()