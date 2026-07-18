import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_tool.pdf_to_text import batch_convert_pdf_to_text


def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(test_dir, "output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"测试目录: {test_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 50)
    
    results = batch_convert_pdf_to_text(
        input_dir=test_dir,
        output_dir=output_dir
    )
    
    print("=" * 50)
    print("测试完成！")
    print(f"转换文件数: {len(results)}")
    for result in results:
        print(f"  - {os.path.basename(result)}")
    
    print("\n请检查 output 目录中的TXT文件是否准确。")


if __name__ == "__main__":
    main()