import os


def _output_path(pdf_path: str, output_path: str | None, suffix: str) -> str:
    if output_path is None:
        directory = os.path.dirname(pdf_path)
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(directory, f"{name}{suffix}.pdf")
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return output_path


def _require_password(password: str) -> str:
    if not isinstance(password, str) or not password.strip():
        raise ValueError("请填写口令")
    if len(password) > 128:
        raise ValueError("口令过长")
    return password


def encrypt_pdf(pdf_path: str, password: str, output_path: str | None = None) -> str:
    import fitz

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    password = _require_password(password)
    output_path = _output_path(pdf_path, output_path, "_encrypted")

    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ValueError(f"这份 PDF 已经加密: {pdf_path}")
        permissions = (
            fitz.PDF_PERM_ACCESSIBILITY
            | fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        )
        doc.save(
            output_path,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw=password,
            owner_pw=password,
            permissions=permissions,
        )
    finally:
        doc.close()

    print(f"加密完成，结果保存到: {output_path}")
    return output_path


def decrypt_pdf(pdf_path: str, password: str, output_path: str | None = None) -> str:
    import fitz

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    password = _require_password(password)
    output_path = _output_path(pdf_path, output_path, "_decrypted")

    print("读取PDF文件...")
    doc = fitz.open(pdf_path)
    try:
        if not doc.is_encrypted:
            raise ValueError(f"这份 PDF 没有加密: {pdf_path}")
        if not doc.authenticate(password):
            raise ValueError("口令不正确")
        doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    finally:
        doc.close()

    print(f"解密完成，结果保存到: {output_path}")
    return output_path


def _pdf_names(input_dir: str) -> list[str]:
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    return [name for name in os.listdir(input_dir) if name.lower().endswith(".pdf")]


def batch_encrypt_pdf(input_dir, password, output_dir=None):
    if output_dir is None:
        output_dir = input_dir
    names = _pdf_names(input_dir)
    if not names:
        print("未找到PDF文件")
        return []
    results = []
    for pdf_file in names:
        name = os.path.splitext(pdf_file)[0]
        target = os.path.join(output_dir, f"{name}_encrypted.pdf")
        try:
            results.append(encrypt_pdf(os.path.join(input_dir, pdf_file), password, output_path=target))
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"处理 {pdf_file} 失败: {exc}")
    return results


def batch_decrypt_pdf(input_dir, password, output_dir=None):
    if output_dir is None:
        output_dir = input_dir
    names = _pdf_names(input_dir)
    if not names:
        print("未找到PDF文件")
        return []
    results = []
    for pdf_file in names:
        name = os.path.splitext(pdf_file)[0]
        target = os.path.join(output_dir, f"{name}_decrypted.pdf")
        try:
            results.append(decrypt_pdf(os.path.join(input_dir, pdf_file), password, output_path=target))
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"处理 {pdf_file} 失败: {exc}")
    return results


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="PDF加密和解密工具")
    subparsers = parser.add_subparsers(dest="command")
    encrypt_parser = subparsers.add_parser("encrypt", help="加密PDF")
    encrypt_parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    encrypt_parser.add_argument("-p", "--password", required=True, help="口令")
    encrypt_parser.add_argument("-o", "--output", help="输出文件路径或目录")
    decrypt_parser = subparsers.add_parser("decrypt", help="解密PDF")
    decrypt_parser.add_argument("pdf_path", help="PDF文件路径或包含PDF的目录路径")
    decrypt_parser.add_argument("-p", "--password", required=True, help="口令")
    decrypt_parser.add_argument("-o", "--output", help="输出文件路径或目录")
    args = parser.parse_args()

    if args.command == "encrypt":
        runner = encrypt_pdf if os.path.isfile(args.pdf_path) else batch_encrypt_pdf
    elif args.command == "decrypt":
        runner = decrypt_pdf if os.path.isfile(args.pdf_path) else batch_decrypt_pdf
    else:
        parser.print_help()
        sys.exit(0)

    if os.path.isfile(args.pdf_path):
        runner(args.pdf_path, args.password, output_path=args.output)
    elif os.path.isdir(args.pdf_path):
        runner(args.pdf_path, args.password, output_dir=args.output)
    else:
        print(f"路径不存在: {args.pdf_path}")
