import os
import sys
import time
import threading


PACKAGE_DIR = os.path.dirname(__file__)

DEFAULT_WECHAT_OCR_RES_DIR = os.path.join(PACKAGE_DIR, 'wechat_ocr_res')


THIRD_PARTY_DIR = os.path.join(PACKAGE_DIR, 'third_party')
if THIRD_PARTY_DIR not in sys.path:
    sys.path.insert(0, THIRD_PARTY_DIR)


def get_default_wechat_path():
    return DEFAULT_WECHAT_OCR_RES_DIR


def get_default_wechatocr_exe():
    return os.path.join(DEFAULT_WECHAT_OCR_RES_DIR, 'WeChatOCR.exe')


class WeChatOCR:
    """
    微信OCR识别类，使用项目内置的OCR资源
    """

    def __init__(self, wechat_path=None, wechatocr_path=None):
        self.wechat_path = wechat_path if wechat_path else get_default_wechat_path()
        self.wechatocr_path = wechatocr_path if wechatocr_path else get_default_wechatocr_exe()
        self.ocr_manager = None
        self._is_running = False
        self._lock = threading.Lock()
        self._result_container = {}

        if not os.path.isdir(self.wechat_path):
            raise FileNotFoundError(f"微信资源目录不存在: {self.wechat_path}")

        if not os.path.isfile(self.wechatocr_path):
            raise FileNotFoundError(f"WeChatOCR.exe 不存在: {self.wechatocr_path}")

    def _callback(self, img_path, results):
        self._result_container[img_path] = results

    def _init_and_start(self):
        from wechat_ocr.ocr_manager import OcrManager

        self.ocr_manager = OcrManager(self.wechat_path)
        self.ocr_manager.SetExePath(self.wechatocr_path)
        self.ocr_manager.SetUsrLibDir(self.wechat_path)
        self.ocr_manager.SetOcrResultCallback(self._callback)
        self.ocr_manager.StartWeChatOCR()
        self._is_running = True

    def ocr(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        image_path = os.path.abspath(image_path)

        with self._lock:
            if not self._is_running:
                self._init_and_start()

        from wechat_ocr.ocr_manager import OCR_MAX_TASK_ID

        self._result_container.pop(image_path, None)

        try:
            self.ocr_manager.DoOCRTask(image_path)
            time.sleep(0.5)
            for _ in range(50):
                if image_path in self._result_container:
                    break
                time.sleep(0.2)

            results = self._result_container.get(image_path, {})
            ocr_result = results.get('ocrResult', [])

            ocr_response = []
            for item in ocr_result:
                ocr_response.append({
                    'text': item.get('text', ''),
                    'left': item.get('location', {}).get('left', 0),
                    'top': item.get('location', {}).get('top', 0),
                    'right': item.get('location', {}).get('right', 0),
                    'bottom': item.get('location', {}).get('bottom', 0),
                })

            return {'ocr_response': ocr_response}

        except Exception as e:
            self._is_running = False
            raise e

    def stop(self):
        if self._is_running and self.ocr_manager:
            self.ocr_manager.KillWeChatOCR()
            self._is_running = False

    def __del__(self):
        self.stop()


def wechat_ocr(image_path, wechat_path=None, wechatocr_path=None):
    """
    使用微信OCR识别图片中的文字（函数式接口，每次创建新实例）
    """
    ocr = WeChatOCR(wechat_path, wechatocr_path)
    try:
        result = ocr.ocr(image_path)
        all_text = ''
        for item in result.get('ocr_response', []):
            all_text += "\n" + item.get('text', '')
        return all_text.strip()
    finally:
        ocr.stop()