# PDF工具包 - 技术文档

## 1. 技术架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户层（User Layer）                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  命令行接口   │  │  Python库接口 │  │  测试脚本    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│                        业务层（Business Layer）                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              pdf_to_text.py (PDF转文本模块)                    │  │
│  │  - convert_pdf_to_text()     # 单文件转换                     │  │
│  │  - batch_convert_pdf_to_text() # 批量转换                     │  │
│  │  - convert_pdf_to_text_with_ocr() # 内部方法                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              pdf_to_image.py (PDF转图片模块)                   │  │
│  │  - convert_pdf_to_images()   # 单文件转换                     │  │
│  │  - batch_convert_pdf_to_images() # 批量转换                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           pdf_split_merge.py (PDF拆分/合并/删除模块)          │  │
│  │  - split_pdf()              # PDF拆分                        │  │
│  │  - merge_pdfs()             # PDF合并                        │  │
│  │  - delete_pages()           # 删除页面                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              pdf_compress.py (PDF压缩模块)                     │  │
│  │  - compress_pdf()            # PDF压缩                        │  │
│  │  - batch_compress_pdf()      # 批量压缩                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │           pdf_to_office.py (PDF转Office模块)                  │  │
│  │  - convert_pdf_to_word()     # PDF转Word                     │  │
│  │  - convert_pdf_to_excel()    # PDF转Excel                    │  │
│  │  - batch_convert_pdf_to_word() # 批量转Word                  │  │
│  │  - batch_convert_pdf_to_excel() # 批量转Excel               │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                        OCR层（OCR Layer）                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              wechat_ocr.py (微信OCR封装)                      │  │
│  │  - WeChatOCR 类              # OCR管理器                      │  │
│  │  - wechat_ocr() 函数         # 便捷接口                       │  │
│  │  - get_default_wechat_path() # 获取默认路径                   │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                  第三方依赖层（Third Party Layer）                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │            third_party/wechat_ocr/                           │  │
│  │  - ocr_manager.py           # OCR核心管理器                   │  │
│  │  - xplugin_manager.py       # 插件管理器                      │  │
│  │  - mmmojo_dll.py            # DLL加载管理                     │  │
│  │  - winapi.py                # Windows API封装                 │  │
│  │  - default_callback.py      # 默认回调函数                    │  │
│  │  - ocr_protobuf_pb2.py      # OCR协议定义                     │  │
│  │  - utility_protobuf_pb2.py  # 工具协议定义                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                  资源层（Resource Layer）                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │            wechat_ocr_res/                                   │  │
│  │  - WeChatOCR.exe            # OCR执行程序                     │  │
│  │  - mmmojo_64.dll            # 核心依赖库                      │  │
│  │  - Model/                   # OCR模型目录                     │  │
│  │  - *.dll                    # 系统依赖库                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责说明

| 模块 | 文件 | 职责 |
|------|------|------|
| PDF转文本 | pdf_to_text.py | 负责PDF转图片、调用OCR、合并结果、保存文件 |
| PDF转图片 | pdf_to_image.py | 负责PDF转图片，支持多种格式和分辨率 |
| PDF拆分/合并/删除 | pdf_split_merge.py | 负责PDF拆分、合并和删除页面操作 |
| PDF压缩 | pdf_compress.py | 负责PDF文件压缩，支持多级别压缩 |
| PDF转Office | pdf_to_office.py | 负责PDF转Word和Excel格式 |
| OCR封装 | wechat_ocr.py | 封装微信OCR调用，提供简洁的API接口 |
| OCR核心 | third_party/wechat_ocr/ocr_manager.py | 管理OCR服务生命周期，处理任务队列 |
| 插件管理 | third_party/wechat_ocr/xplugin_manager.py | 管理微信XPlugin环境，加载DLL |
| DLL加载 | third_party/wechat_ocr/mmmojo_dll.py | 封装mmmojo.dll的加载和调用 |
| Windows API | third_party/wechat_ocr/winapi.py | 封装Windows API调用 |
| 协议定义 | third_party/wechat_ocr/*_protobuf_pb2.py | 定义OCR通信协议 |

## 2. 核心技术实现

### 2.1 PDF转图片

**技术方案**：使用 `pdf2image` 库将PDF转换为图片

**实现原理**：
```python
from pdf2image import convert_from_path

images = convert_from_path(pdf_path)
for i, image in enumerate(images):
    image.save(os.path.join(image_dir, f"page_{i+1}.png"))
```

**关键依赖**：
- `pdf2image`：Python库，封装poppler工具
- `poppler`：PDF渲染引擎，需要用户手动安装

### 2.2 微信OCR识别

**技术方案**：使用微信OCR引擎进行文字识别

**实现原理**：

1. **初始化OCR服务**：
   - 加载 `mmmojo_64.dll`
   - 创建XPlugin环境
   - 启动 `WeChatOCR.exe` 进程

2. **发送OCR任务**：
   - 构建OCR请求协议（Protobuf格式）
   - 通过IPC通道发送请求
   - 等待OCR服务处理

3. **接收识别结果**：
   - 注册回调函数
   - 接收OCR服务返回的结果
   - 解析Protobuf格式的响应

**核心代码流程**：
```python
ocr = WeChatOCR()
result = ocr.ocr(image_path)
# result = {'ocr_response': [{'text': '识别文字', 'left': 0, 'top': 0, ...}]}
```

**线程安全设计**：
- 使用 `threading.Lock()` 保证OCR服务初始化的线程安全
- 使用字典存储识别结果，通过图片路径作为键

### 2.3 结果处理与保存

**处理流程**：
1. 遍历每页OCR识别结果
2. 提取文字内容
3. 过滤短文本页面（长度 < min_text_length）
4. 合并所有页面的文字
5. 保存为UTF-8编码的TXT文件

**批量处理优化**：
- 共享OCR实例，避免重复初始化
- 每个PDF使用独立的图片目录，避免文件冲突
- 使用 `finally` 块确保OCR服务正确关闭

## 3. 目录结构

```
pdf_tool/
├── .trae/                 # Trae AI工具辅助目录（技术规范文档）
│   ├── prd.md             # 产品需求文档
│   └── tech_doc.md        # 技术文档
├── README.md              # 项目说明文档
├── requirements.txt       # 依赖清单
├── tests/                 # 测试目录
│   ├── a.pdf              # 测试PDF文件
│   ├── b.pdf              # 测试PDF文件
│   ├── test_pdf_to_text.py # PDF转文本测试脚本
│   └── test_all_tools.py  # 全功能测试脚本
└── pdf_tool/              # 核心包目录
    ├── __init__.py        # 包入口，导出核心函数
    ├── wechat_ocr.py      # 微信OCR封装模块
    ├── pdf_to_text.py     # PDF转文本模块
    ├── pdf_to_image.py    # PDF转图片模块
    ├── pdf_split_merge.py # PDF拆分、合并和删除模块
    ├── pdf_compress.py    # PDF压缩模块
    ├── pdf_to_office.py   # PDF转Word和Excel模块
    ├── wechat_ocr_res/    # 微信OCR资源目录
    │   ├── WeChatOCR.exe  # OCR执行程序
    │   ├── mmmojo_64.dll  # 核心依赖库（64位）
    │   ├── Model/         # OCR模型文件
    │   └── *.dll          # 系统依赖库
    └── third_party/       # 第三方依赖包（内置）
        └── wechat_ocr/    # wechat-ocr库源码
```

## 4. 关键类与函数

### 4.1 WeChatOCR 类

**文件**：`pdf_tool/wechat_ocr.py`

**功能**：封装微信OCR引擎，提供文字识别功能

**属性**：
| 属性 | 类型 | 说明 |
|------|------|------|
| wechat_path | str | 微信OCR资源路径 |
| wechatocr_path | str | WeChatOCR.exe路径 |
| ocr_manager | OcrManager | OCR管理器实例 |
| _is_running | bool | OCR服务运行状态 |
| _lock | Lock | 线程锁 |
| _result_container | dict | 识别结果容器 |

**方法**：
| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| \_\_init\_\_ | wechat_path, wechatocr_path | - | 初始化OCR实例 |
| ocr | image_path | dict | 识别图片中的文字 |
| stop | - | - | 停止OCR服务 |
| \_\_del\_\_ | - | - | 析构函数，确保资源释放 |

### 4.2 convert_pdf_to_text 函数

**文件**：`pdf_tool/pdf_to_text.py`

**功能**：将PDF文件转换为文本文件

**参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| pdf_path | str | - | PDF文件路径 |
| output_dir | str | None | 输出目录 |
| image_dir | str | None | 临时图片目录 |
| skip_pages | list | None | 跳过的页码列表 |
| min_text_length | int | 50 | 最小文本长度 |
| wechat_path | str | None | 微信OCR资源路径 |
| wechatocr_path | str | None | WeChatOCR.exe路径 |

**返回值**：生成的TXT文件路径（str）

### 4.3 batch_convert_pdf_to_text 函数

**文件**：`pdf_tool/pdf_to_text.py`

**功能**：批量转换目录中的PDF文件

**参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| input_dir | str | - | 输入目录 |
| output_dir | str | None | 输出目录 |
| image_dir | str | None | 临时图片目录 |
| skip_pages | list | None | 跳过的页码列表 |
| min_text_length | int | 50 | 最小文本长度 |
| wechat_path | str | None | 微信OCR资源路径 |
| wechatocr_path | str | None | WeChatOCR.exe路径 |

**返回值**：生成的TXT文件路径列表（list）

## 5. 依赖管理

### 5.1 Python依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| pdf2image | 1.17.0 | PDF转图片 |
| protobuf | >=3.20.3 | 协议序列化/反序列化 |
| PyPDF2 | >=2.10.0 | PDF拆分、合并、删除 |
| PyMuPDF | >=1.22.0 | PDF压缩、转Office |
| python-docx | >=1.1.0 | PDF转Word |
| openpyxl | >=3.1.0 | PDF转Excel |

### 5.2 系统依赖

| 依赖 | 用途 | 获取方式 |
|------|------|----------|
| poppler | PDF渲染引擎 | 手动下载安装 |
| WeChatOCR.exe | OCR执行程序 | 内置 |
| mmmojo_64.dll | 核心依赖库 | 内置 |
| Model/* | OCR模型文件 | 内置 |

### 5.3 第三方包内置

为避免外部依赖更新或失效，以下包已内置到项目中：

| 包 | 版本 | 位置 |
|------|------|------|
| wechat-ocr | 0.0.3 | third_party/wechat_ocr/ |

## 6. 安装与配置

### 6.1 环境要求

- Windows 10/11（64位）
- Python 3.7+
- poppler 工具

### 6.2 安装步骤

1. **安装Python依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **安装poppler**：
   - 下载地址：https://github.com/oschwartz10612/poppler-windows
   - 解压到任意目录
   - 将 `bin` 目录添加到系统环境变量 `PATH`

3. **验证安装**：
   ```bash
   python -c "from pdf2image import convert_from_path; print('pdf2image 安装成功')"
   ```

### 6.3 配置说明

**默认配置**：
- OCR资源路径：`pdf_tool/wechat_ocr_res/`
- WeChatOCR.exe路径：`pdf_tool/wechat_ocr_res/WeChatOCR.exe`

**自定义配置**：
可通过函数参数指定自定义路径：
```python
convert_pdf_to_text(
    pdf_path="example.pdf",
    wechat_path="custom/path/to/wechat_ocr_res",
    wechatocr_path="custom/path/to/WeChatOCR.exe"
)
```

## 7. API接口

### 7.1 命令行接口

```bash
# 转换单个PDF文件
python -m pdf_tool.pdf_to_text example.pdf

# 指定输出目录
python -m pdf_tool.pdf_to_text example.pdf -o output/

# 转换目录中的所有PDF
python -m pdf_tool.pdf_to_text pdf_directory/

# 跳过指定页码（从1开始）
python -m pdf_tool.pdf_to_text example.pdf -s 1 2 3

# 设置最小文本长度
python -m pdf_tool.pdf_to_text example.pdf -m 100

# 自定义微信OCR路径
python -m pdf_tool.pdf_to_text example.pdf -w wechat_path -c ocr_path
```

### 7.2 Python库接口

```python
from pdf_tool import convert_pdf_to_text
from pdf_tool.pdf_to_text import batch_convert_pdf_to_text

# 转换单个PDF
txt_path = convert_pdf_to_text(
    pdf_path="example.pdf",
    output_dir="output/",
    skip_pages=[0, 1],        # 跳过第1、2页（从0开始）
    min_text_length=50
)

# 批量转换
results = batch_convert_pdf_to_text(
    input_dir="pdf_directory/",
    output_dir="output/"
)
```

### 7.3 OCR接口

```python
from pdf_tool.wechat_ocr import WeChatOCR, wechat_ocr

# 使用类接口
ocr = WeChatOCR()
result = ocr.ocr("image.png")
text = ""
for item in result['ocr_response']:
    text += item['text'] + "\n"
ocr.stop()

# 使用函数接口
text = wechat_ocr("image.png")
```

## 8. 测试方案

### 8.1 测试环境

- Windows 10/11
- Python 3.7/3.12
- 测试PDF文件：a.pdf（62页）、b.pdf（51页）

### 8.2 测试用例

**功能测试**：
| 用例 | 描述 | 预期结果 |
|------|------|----------|
| TC001 | 转换单页PDF | 生成包含识别文字的TXT文件 |
| TC002 | 转换多页PDF | 生成完整的TXT文件，包含所有页面内容 |
| TC003 | 批量转换 | 正确处理目录中的所有PDF文件 |
| TC004 | 跳过页码 | 指定页码被正确跳过 |
| TC005 | 过滤短文本 | 短文本页面被正确过滤 |

**性能测试**：
| 用例 | 描述 | 预期结果 |
|------|------|----------|
| TP001 | 单页转换时间 | ≤ 2秒 |
| TP002 | 60页转换时间 | ≤ 120秒 |

**兼容性测试**：
| 用例 | 描述 | 预期结果 |
|------|------|----------|
| TC001 | Windows 10 | 正常运行 |
| TC002 | Windows 11 | 正常运行 |
| TC003 | Python 3.7 | 正常运行 |
| TC004 | Python 3.12 | 正常运行 |

### 8.3 测试脚本

**批量测试**：
```bash
python tests/test_pdf_to_text.py
```

**单文件测试**：
```bash
python tests/test_b_pdf.py
```

**命令行测试**：
```bash
python -m pdf_tool.pdf_to_text tests/a.pdf -o tests/output/
```

## 9. 部署与发布

### 9.1 开发环境

```bash
# 克隆项目
git clone https://github.com/chenyunxing/pdf_tool.git

# 进入项目目录
cd pdf_tool

# 安装依赖
pip install -r requirements.txt

# 运行测试
python tests/test_pdf_to_text.py
```

### 9.2 生产环境

```bash
# 安装包
pip install .

# 使用
python -m pdf_tool.pdf_to_text example.pdf
```

### 9.3 打包发布

使用 PyInstaller 打包为可执行文件：

```bash
pip install pyinstaller
pyinstaller --onefile --name pdf_tool pdf_tool/pdf_to_text.py
```

## 10. 代码规范

### 10.1 命名规范

- 模块名：小写，使用下划线分隔（如 `pdf_to_text.py`）
- 类名：大驼峰式（如 `WeChatOCR`）
- 函数名：小写，使用下划线分隔（如 `convert_pdf_to_text`）
- 变量名：小写，使用下划线分隔（如 `image_dir`）
- 常量名：全大写，使用下划线分隔（如 `DEFAULT_WECHAT_OCR_RES_DIR`）

### 10.2 代码风格

- 使用4个空格缩进
- 行长度不超过120字符
- 使用类型提示
- 添加适当的注释
- 遵循PEP 8规范

### 10.3 错误处理

- 使用 try/except 捕获异常
- 提供清晰的错误信息
- 使用 finally 块确保资源释放
- 避免使用裸 except

## 11. 扩展建议

### 11.1 添加新工具

在 `pdf_tool/` 目录下添加新模块，如：
- `pdf_encrypt.py`：PDF加密/解密功能
- `pdf_rotate.py`：PDF页面旋转功能
- `pdf_watermark.py`：PDF水印功能

### 11.2 增加配置文件

创建 `config.yaml` 配置文件，统一管理路径和参数。

### 11.3 支持更多平台

当前仅支持Windows，可考虑添加：
- Linux平台支持（使用Tesseract OCR）
- macOS平台支持

### 11.4 添加图形界面

使用PyQt或Tkinter创建GUI界面，方便非技术用户使用。