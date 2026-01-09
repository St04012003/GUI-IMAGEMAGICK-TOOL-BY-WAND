from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot
from wand.image import Image as WandImage

from core import CommandParser

# ================
# Preview Engine
# ================

# === Data Transfer Objects ===

class PreviewRequest:
    """Gói dữ liệu yêu cầu xử lý"""
    def __init__(self, request_id: int, image_blob: bytes, command_string: str):
        self.request_id = request_id
        self.image_blob = image_blob
        self.command_string = command_string


class PreviewResult:
    """Gói dữ liệu kết quả trả về"""
    def __init__(self, request_id: int, image_blob: bytes = None, error: str = None):
        self.request_id = request_id
        self.image_blob = image_blob
        self.error = error


# === Async Task Processor (Worker Thread) ===

class AsyncTaskProcessor(QObject):
    """
    Worker xử lý ảnh chạy trên Thread riêng biệt vĩnh viễn.
    Sử dụng signal để giao tiếp, không bao giờ bị kill đột ngột.
    """
    result_signal = pyqtSignal(PreviewResult)

    def __init__(self):
        super().__init__()
        self._is_busy = False
        self._pending_request = None  # Chỉ giữ request mới nhất

    @pyqtSlot(object)
    def process_request(self, request: PreviewRequest):
        """
        Nhận request từ UI thread.
        Nếu đang bận, lưu request mới nhất vào queue (ghi đè cái cũ).
        """
        if self._is_busy:
            self._pending_request = request
            return

        self._execute(request)

    def _execute(self, request: PreviewRequest):
        """
        Xử lý request với vòng lặp thay vì đệ quy.
        Tránh stack overflow khi user gõ phím liên tục.
        """
        current_req = request
        
        while current_req:
            self._is_busy = True
            
            try:
                # Xử lý ảnh (phần nặng)
                out_blob = self._process_image(current_req)
                
                # Gửi kết quả về UI
                self.result_signal.emit(
                    PreviewResult(current_req.request_id, image_blob=out_blob)
                )

            except Exception as e:
                self.result_signal.emit(
                    PreviewResult(current_req.request_id, error=str(e))
                )
            
            finally:
                self._is_busy = False
                
                # Lấy request tiếp theo (nếu có) và tiếp tục vòng lặp
                current_req = self._pending_request
                self._pending_request = None

    def _process_image(self, request: PreviewRequest) -> bytes:
        """Xử lý ảnh với ImageMagick"""
        with WandImage(blob=request.image_blob) as img:
            if request.command_string:
                operations = CommandParser.parse(request.command_string)
                CommandParser.apply_commands(img, operations)
            
            return img.make_blob(format='bmp')


# === Preview Controller (UI Thread) ===

class PreviewController(QObject):
    """
    Controller nằm ở UI Thread, quản lý việc gửi request.
    Đảm bảo ID request luôn tăng dần để UI không hiển thị kết quả cũ.
    """
    request_signal = pyqtSignal(PreviewRequest)  # Gửi đi cho Worker
    preview_ready_signal = pyqtSignal(bytes)     # Gửi blob ảnh về cho UI chính

    def __init__(self):
        super().__init__()
        
        # Khởi tạo worker thread
        self.worker_thread = QThread()
        self.worker = AsyncTaskProcessor()
        
        # Di chuyển worker vào thread
        self.worker.moveToThread(self.worker_thread)
        
        # Kết nối signals
        self.request_signal.connect(self.worker.process_request)
        self.worker.result_signal.connect(self._handle_result)
        
        # Quản lý ID
        self._req_counter = 0
        
        # Khởi động thread
        self.worker_thread.start()

    def request_preview(self, image_blob: bytes, command_string: str):
        """
        UI gọi hàm này để yêu cầu preview.
        Mỗi lần gọi tạo request ID mới.
        """
        if not image_blob: 
            return

        self._req_counter += 1
        req = PreviewRequest(self._req_counter, image_blob, command_string)
        self.request_signal.emit(req)

    def _handle_result(self, result: PreviewResult):
        """
        Nhận kết quả từ Worker.
        Chỉ chấp nhận kết quả có ID bằng request mới nhất.
        """
        # QUAN TRỌNG: Chỉ chấp nhận kết quả mới nhất
        if result.request_id < self._req_counter:
            # Đây là kết quả của lệnh cũ (do gõ phím quá nhanh), vứt bỏ
            return

        if result.error:
            print(f"Preview Error: {result.error}")
        elif result.image_blob:
            self.preview_ready_signal.emit(result.image_blob)
    
    def shutdown(self):
        """Dọn dẹp sạch sẽ khi tắt app"""
        self.worker_thread.quit()
        self.worker_thread.wait()