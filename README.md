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
| **pdf_rotate** | 顺时针旋转页面 | ✅ 可用 |
| **pdf_watermark** | 添加斜放文字水印 | ✅ 可用 |
| **pdf_crypto** | 加密和解密 | ✅ 可用 |

## 安装依赖

```bash
pip install -r requirements.txt
```

**环境要求**：
- Python 3.7+
- Windows系统
- poppler 已内置在 `pdf_tool/third_party/poppler-26.09.0`，无需单独安装

## 使用方法

### 1. 作为库使用

```python
from pdf_tool import convert_pdf_to_text, convert_pdf_to_images, split_pdf, merge_pdfs, delete_pages, compress_pdf, convert_pdf_to_word, convert_pdf_to_excel, rotate_pdf, add_watermark, encrypt_pdf, decrypt_pdf

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

# 顺时针旋转 90 度
rotated_path = rotate_pdf("example.pdf", angle=90)

# 只旋转第 1 到第 3 页，其余页不变
rotated_path = rotate_pdf("example.pdf", angle=180, start_page=1, end_page=3)

# 添加水印
watermarked_path = add_watermark("example.pdf", "草稿")

# 加密、解密
encrypted_path = encrypt_pdf("example.pdf", "secret")
decrypted_path = decrypt_pdf(encrypted_path, "secret")
```

### 2. 命令行使用

```bash
# pdf转文字，转换单个PDF文件
python -m pdf_tool.pdf_to_text example.pdf

# pdf转文字，转换目录中的所有PDF文件
python -m pdf_tool.pdf_to_text pdf_directory/

# pdf转文字，指定输出目录
python -m pdf_tool.pdf_to_text example.pdf -o output/

# pdf转文字，跳过指定页码（从1开始）
python -m pdf_tool.pdf_to_text example.pdf -s 1 2 3

# 拆分PDF文件（每页一个文件）
python -m pdf_tool.pdf_split_merge split example.pdf -o output/split/

# 拆分PDF文件（每5页一个文件）
python -m pdf_tool.pdf_split_merge split example.pdf -p 5

# 拆分PDF指定页码范围(每页一个文件，如果要指定大小需要-p参数)
python -m pdf_tool.pdf_split_merge split example.pdf -s 10 -e 20

# 合并多个PDF文件
python -m pdf_tool.pdf_split_merge merge file1.pdf file2.pdf -o merged.pdf

# 删除PDF指定页码
python -m pdf_tool.pdf_split_merge delete example.pdf 1 5 10 -o output.pdf

# 删除时只保留第 1 到第 10 页，再去掉其中的第 2 页
python -m pdf_tool.pdf_split_merge delete example.pdf 2 -s 1 -e 10

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

# 只压缩第 1 到第 5 页
python -m pdf_tool.pdf_compress example.pdf -s 1 -e 5

# PDF转Word
python -m pdf_tool.pdf_to_office word example.pdf -o output/

# PDF转Word（包含图片）
python -m pdf_tool.pdf_to_office word example.pdf -i

# PDF转Word（指定页码范围）
python -m pdf_tool.pdf_to_office word example.pdf -s 1 -e 5

# PDF转Excel
python -m pdf_tool.pdf_to_office excel example.pdf -o output/

# PDF转Excel（仅提取表格）
python -m pdf_tool.pdf_to_office excel example.pdf -t

# PDF转Excel（指定页码范围）
python -m pdf_tool.pdf_to_office excel example.pdf -s 1 -e 5

# 顺时针旋转
python -m pdf_tool.pdf_rotate example.pdf -a 90

# 只旋转第 1 到第 3 页
python -m pdf_tool.pdf_rotate example.pdf -a 180 -s 1 -e 3

# 添加水印
python -m pdf_tool.pdf_watermark example.pdf -t 草稿

# 加密、解密
python -m pdf_tool.pdf_crypto encrypt example.pdf -p secret
python -m pdf_tool.pdf_crypto decrypt example_encrypted.pdf -p secret
```

### 3. 网页工作台

在项目根目录启动。页面只在这台电脑上处理文件，并允许同一局域网里的设备打开，不设口令。

```bash
python web/app.py
```

浏览器打开 http://127.0.0.1:8765 。页面上会写出局域网地址。手机若打不开，在 Windows 防火墙中允许该端口。

左侧导航切换工具。不打开「高级」时，使用各工具的默认参数。多份文件按队列逐份处理；合并按名单顺序接成一份。结果留在 `web/data/`。已经结束的任务，页面上的时间超过一天后，连同文件一起删除。等候或进行中的任务会留下。转文字可以在页面里阅读，转图片可以按页翻看。

预览一次打开一份 PDF，按页查看。正在看的那一页可以加水印、提取文字、顺时针旋转 90 度或删除。改过的文件仍留在这份预览里，也可以下载。已经有文字的页直接取出文字；几乎没有文字、只有扫描图像的页会先识别。加密的 PDF 要先解密再预览。

### 4. 完整示例

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
| image_dir | 临时图片目录，每页识别后删除，目录为空则删除 | output_dir/images/{pdf名} |
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
| start_page | 起始页码（从1开始）。填写后，结果只保留这一段 | 1 |
| end_page | 结束页码（从1开始），含本页 | 最后一页 |

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
| start_page | 起始页码（从1开始）。填写后，结果只包含这一段 | 1 |
| end_page | 结束页码（从1开始），含本页 | 最后一页 |

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
| start_page | 起始页码（从1开始） | 1 |
| end_page | 结束页码（从1开始），含本页 | 最后一页 |

某一页几乎没有可选中的文字，并且页面上是扫描图像时，用微信 OCR 识别后写入。已经有文字层的页不识别。

### convert_pdf_to_excel 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}.xlsx |
| table_only | 是否仅提取表格 | False |
| start_page | 起始页码（从1开始） | 1 |
| end_page | 结束页码（从1开始），含本页 | 最后一页 |

某一页几乎没有可选中的文字，并且页面上是扫描图像时，用微信 OCR 识别后按行写入。已经有文字层的页不识别。勾选只导出表格时，有文字层的页只保留表格，扫描页仍写入识别出的文字。

### rotate_pdf 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| angle | 顺时针角度，只接受 90、180、270 | 90 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}_rotated.pdf |
| start_page | 起始页码（从1开始）。填写后，只转这一段 | 1 |
| end_page | 结束页码（从1开始），含本页。其余页不变 | 最后一页 |

### add_watermark 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| text | 水印文字，最多 80 个字 | 必填 |
| output_path | 输出文件路径 | PDF所在目录/{pdf_name}_watermarked.pdf |
| start_page | 起始页码（从1开始）。填写后，只加在这一段 | 1 |
| end_page | 结束页码（从1开始），含本页。其余页不变 | 最后一页 |

### encrypt_pdf / decrypt_pdf 工具

| 参数 | 说明 | 默认值 |
|------|------|--------|
| pdf_path | PDF文件路径或包含PDF的目录 | 必填 |
| password | 口令 | 必填 |
| output_path | 输出文件路径 | 加密为 {pdf_name}_encrypted.pdf，解密为 {pdf_name}_decrypted.pdf |

加密后没有口令打不开。解密口令不正确时不会写出文件。

## 工作原理

pdf_to_text 工具的处理流程：

1. **逐页转图片并识别**：用内置 poppler 将当前页转为 PNG，马上用微信 OCR 识别，然后删除该图片
2. **立刻写入**：过滤掉短文本页面后，把该页文字追加到 TXT
3. **结束清理**：删除空的临时图片目录

## 注意事项

1. **poppler**：pdf2image 使用项目内置的 `pdf_tool/third_party/poppler-26.09.0/Library/bin`，不依赖系统 PATH
2. **仅支持Windows**：微信OCR引擎基于Windows平台
3. **OCR资源内置**：项目已内置微信OCR资源，无需安装微信客户端
4. **Python版本**：建议使用Python 3.7及以上版本

## 项目结构

```
pdf_tool/
├── .cursor/rules/        # Cursor 项目规则
│   ├── project.mdc       # 产品边界与平台约束
│   ├── python.mdc        # Python 规范
│   └── pdf-modules.mdc   # 模块 API 与 OCR 约定
├── pdf_tool/             # 核心包目录
│   ├── __init__.py       # 包入口，导出核心函数
│   ├── wechat_ocr.py     # 微信OCR模块（封装OCR调用）
│   ├── pdf_to_text.py    # PDF转文本工具（核心功能）
│   ├── pdf_to_image.py   # PDF转图片工具
│   ├── pdf_compress.py   # PDF压缩工具
│   ├── pdf_to_office.py  # PDF转Word和Excel工具
│   ├── pdf_rotate.py     # 旋转页面
│   ├── pdf_watermark.py  # 添加水印
│   ├── pdf_crypto.py     # 加密和解密
│   ├── pdf_split_merge.py # PDF拆分、合并和删除工具
│   ├── wechat_ocr_res/   # 微信OCR资源目录
│   │   ├── WeChatOCR.exe # OCR执行程序
│   │   ├── mmmojo_64.dll # 核心依赖库（64位）
│   │   ├── Model/        # OCR模型文件
│   │   └── *.dll         # 系统依赖库
│   └── third_party/      # 第三方依赖包（内置）
│       ├── wechat_ocr/   # wechat-ocr 库源码
│       └── poppler-26.09.0/ # poppler，可执行文件在 Library/bin
├── web/                  # 本机网页工作台
│   ├── app.py            # 页面与接口
│   ├── engine.py         # 任务队列
│   └── static/           # 页面资源
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
- v0.6.0：添加本机网页工作台
- v0.7.0：删页、压缩、转 Word、转 Excel 支持页范围；转图片可在页面翻看；转 Word 按阅读顺序写入文字、表格和图片
- v0.8.0：转 Word 会识别几乎没有文字层的扫描页
- v0.9.0：添加旋转、水印、加密和解密
- v0.10.0：转 Excel 会识别几乎没有文字层的扫描页
- v0.11.0：工作台里已经结束、超过一天的任务会自动删除
- v0.12.0：工作台可以预览 PDF，并对当前页加水印、提取文字、旋转或删除