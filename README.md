# pdf_tool

PDF处理工具包，提供多种PDF相关功能。

## 工具列表

| 工具名称 | 功能描述 | 状态 |
|---------|---------|------|
| **pdf_to_text** | 使用微信OCR将PDF转换为文本 | ✅ 可用 |
| **pdf_to_image** | 将PDF转换为图片 | ✅ 可用 |
| **pdf_split_merge** | PDF文件拆分、合并和删除 | ✅ 可用 |
| **pdf_compress** | PDF文件压缩 | ✅ 可用 |
| **pdf_to_office** | PDF转Word和Excel | ✅ 可用 |

## 安装依赖

```bash
pip install -r requirements.txt
```

**环境要求**：
- Python 3.7+
- Windows系统
- 需要安装poppler（pdf2image依赖）

## 使用方法

### 1. 作为库使用

```python
from pdf_tool import convert_pdf_to_text, convert_pdf_to_images, split_pdf, merge_pdfs, delete_pages, compress_pdf, convert_pdf_to_word, convert_pdf_to_excel

# 转换单个PDF文件
txt_path = convert_pdf_to_text("example.pdf")

# 转换多个PDF文件
from pdf_tool.pdf_to_text import batch_convert_pdf_to_text
results = batch_convert_pdf_to_text("pdf_directory/")

# PDF转图片
image_paths = convert_pdf_to_images("example.pdf", output_dir="output/images/")

# PDF转图片（指定格式和分辨率）
image_paths = convert_pdf_to_images("example.pdf", image_format="jpg", dpi=300)

# PDF转图片（指定页码范围）
image_paths = convert_pdf_to_images("example.pdf", start_page=10, end_page=20)

# 拆分PDF文件（每页一个文件）
split_results = split_pdf("example.pdf", output_dir="output/split/")

# 拆分PDF文件（每5页一个文件）
split_results = split_pdf("example.pdf", pages_per_file=5)

# 合并多个PDF文件
merged_path = merge_pdfs(["file1.pdf", "file2.pdf", "file3.pdf"])

# 删除PDF指定页码
deleted_path = delete_pages("example.pdf", pages_to_delete=[1, 5, 10])

# 压缩PDF文件
result = compress_pdf("example.pdf", output_path="output/compressed.pdf")

# 压缩PDF文件（指定压缩级别）
result = compress_pdf("example.pdf", compression_level=5)

# PDF转Word
word_path = convert_pdf_to_word("example.pdf", output_path="output/example.docx")

# PDF转Word（包含图片）
word_path = convert_pdf_to_word("example.pdf", include_images=True)

# PDF转Excel
excel_path = convert_pdf_to_excel("example.pdf", output_path="output/example.xlsx")

# PDF转Excel（仅提取表格）
excel_path = convert_pdf_to_excel("example.pdf", table_only=True)
```

### 2. 命令行使用

```bash
# 转换单个PDF文件
python -m pdf_tool.pdf_to_text example.pdf

# 转换目录中的所有PDF文件
python -m pdf_tool.pdf_to_text pdf_directory/

# 指定输出目录
python -m pdf_tool.pdf_to_text example.pdf -o output/

# 跳过指定页码（从1开始）
python -m pdf_tool.pdf_to_text example.pdf -s 1 2 3

# 拆分PDF文件（每页一个文件）
python -m pdf_tool.pdf_split_merge split example.pdf -o output/split/

# 拆分PDF文件（每5页一个文件）
python -m pdf_tool.pdf_split_merge split example.pdf -p 5

# 拆分PDF指定页码范围
python -m pdf_tool.pdf_split_merge split example.pdf -s 10 -e 20

# 合并多个PDF文件
python -m pdf_tool.pdf_split_merge merge file1.pdf file2.pdf -o merged.pdf

# 删除PDF指定页码
python -m pdf_tool.pdf_split_merge delete example.pdf 1 5 10 -o output.pdf

# PDF转图片
python -m pdf_tool.pdf_to_image example.pdf -o output/images/

# PDF转图片（指定格式）
python -m pdf_tool.pdf_to_image example.pdf -f jpg

# PDF转图片（指定分辨率）
python -m pdf_tool.pdf_to_image example.pdf -d 300

# PDF转图片（指定页码范围）
python -m pdf_tool.pdf_to_image example.pdf -s 10 -e 20

# 压缩PDF文件
python -m pdf_tool.pdf_compress example.pdf -o output/compressed.pdf

# 压缩PDF文件（指定压缩级别）
python -m pdf_tool.pdf_compress example.pdf -c 5

# PDF转Word
python -m pdf_tool.pdf_to_office word example.pdf -o output/

# PDF转Word（包含图片）
python -m pdf_tool.pdf_to_office word example.pdf -i

# PDF转Excel
python -m pdf_tool.pdf_to_office excel example.pdf -o output/

# PDF转Excel（仅提取表格）
python -m pdf_tool.pdf_to_office excel example.pdf -t
```

### 3. 完整示例

```python
from pdf_tool import convert_pdf_to_text

# 转换PDF为文本
result = convert_pdf_to_text(
    pdf_path="document.pdf",
    output_dir="output/",
    skip_pages=[0, 1],        # 跳过封面和目录
    min_text_length=50        # 忽略短文本页面
)

print(f"文本已保存到: {result}")
```

## 参数说明

### pdf_to_text 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_dir | 输出目录 | PDF所在目录 |
| image_dir | 临时图片保存目录 | output_dir/images |
| skip_pages | 需要跳过的页码列表（从0开始） | 空列表 |
| min_text_length | 最小文本长度，小于此长度的页面将被忽略 | 50 |
| wechat_path | 微信OCR资源路径 | 项目内wechat_ocr_res目录 |
| wechatocr_path | WeChatOCR.exe路径 | 项目内wechat_ocr_res/WeChatOCR.exe |

### split_pdf 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | 要拆分的PDF文件路径 | 必填 |
| output_dir | 输出目录 | PDF所在目录 |
| pages_per_file | 每个输出文件的页数 | 1 |
| start_page | 起始页码（从1开始） | 1 |
| end_page | 结束页码（从1开始） | 最后一页 |

### merge_pdfs 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_paths | 要合并的PDF文件路径列表 | 必填 |
| output_path | 输出文件路径 | 第一个PDF所在目录/merged_output.pdf |

### delete_pages 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | 要处理的PDF文件路径 | 必填 |
| pages_to_delete | 要删除的页码列表（从1开始） | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}_deleted.pdf |

### convert_pdf_to_images 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_dir | 输出目录 | PDF所在目录/images/{pdf_name} |
| image_format | 输出图片格式（png/jpg/jpeg/ppm/tif/tiff） | png |
| dpi | 图片分辨率（DPI） | 200 |
| start_page | 起始页码（从1开始） | None（第一页） |
| end_page | 结束页码（从1开始） | None（最后一页） |
| clear_existing | 是否清空输出目录中已存在的文件 | True |

### compress_pdf 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}_compressed.pdf |
| compression_level | 压缩级别（1-5，级别越高压缩率越大） | 3 |

**压缩级别说明：**
- **级别1**：基础压缩，仅清理PDF结构
- **级别2**：压缩内容流
- **级别3**：优化图片（默认）
- **级别4**：重新压缩图片
- **级别5**：高压缩率，可能降低图片质量

### convert_pdf_to_word 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}.docx |
| include_images | 是否包含图片 | True |

### convert_pdf_to_excel 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}.xlsx |
| table_only | 是否仅提取表格 | False |

## 工作原理

pdf_to_text 工具的处理流程：

1. **PDF转图片**：使用 `pdf2image` 将PDF的每一页转换为PNG图片
2. **图片OCR识别**：使用内置的微信OCR引擎识别图片中的文字
3. **结果合并**：将每页识别的文字合并，过滤掉短文本页面（如封面）
4. **保存结果**：将最终文本保存为TXT文件

## 注意事项

1. **poppler安装**：需要安装poppler才能使用pdf2image。Windows用户可从[poppler-windows](https://github.com/oschwartz10612/poppler-windows)下载
2. **仅支持Windows**：微信OCR引擎基于Windows平台
3. **OCR资源内置**：项目已内置微信OCR资源，无需安装微信客户端
4. **Python版本**：建议使用Python 3.7及以上版本

## 项目结构

```
pdf_tool/
├── .trae/                # Trae AI工具辅助目录（技术规范文档）
│   ├── prd.md            # 产品需求文档
│   └── tech_doc.md       # 技术文档
├── pdf_tool/             # 核心包目录
│   ├── __init__.py       # 包入口，导出核心函数
│   ├── wechat_ocr.py     # 微信OCR模块（封装OCR调用）
│   ├── pdf_to_text.py    # PDF转文本工具（核心功能）
│   ├── pdf_to_image.py   # PDF转图片工具
│   ├── pdf_compress.py    # PDF压缩工具
│   ├── pdf_to_office.py   # PDF转Word和Excel工具
│   └── pdf_split_merge.py # PDF拆分、合并和删除工具
│   ├── wechat_ocr_res/   # 微信OCR资源目录
│   │   ├── WeChatOCR.exe # OCR执行程序
│   │   ├── mmmojo_64.dll # 核心依赖库（64位）
│   │   ├── Model/        # OCR模型文件
│   │   └── *.dll         # 系统依赖库（40+个）
│   └── third_party/      # 第三方依赖包（内置，避免外部依赖）
│       └── wechat_ocr/   # wechat-ocr 库源码
├── tests/                # 测试目录
├── README.md             # 项目说明文档
└── requirements.txt      # 依赖清单
```

## 许可证

本项目仅供学习和个人使用。

## 更新日志

- v0.1.0：初始版本，实现PDF转文本功能
- v0.2.0：添加PDF拆分、合并和删除页面功能
- v0.3.0：添加PDF转图片功能
- v0.4.0：添加PDF压缩功能
- v0.5.0：添加PDF转Word和PDF转Excel功能