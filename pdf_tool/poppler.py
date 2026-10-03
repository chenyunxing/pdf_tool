import os


def get_poppler_path() -> str:
    bin_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "third_party",
        "poppler-26.09.0",
        "Library",
        "bin",
    )
    pdfinfo = os.path.join(bin_dir, "pdfinfo.exe")
    if not os.path.isfile(pdfinfo):
        raise FileNotFoundError(f"内置 poppler 不存在: {pdfinfo}")
    return bin_dir
