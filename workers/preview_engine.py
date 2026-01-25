from qtpy.QtCore import QThread, Signal, QObject, Slot
from qtpy.QtGui import QImage
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
    def __init__(self, request_id: int, qimage: QImage = None, error: str = None):
        self.request_id = request_id
        self.qimage = qimage 
        self.error = error


# === Original Image Processor (Thread 1) ===
class OriginalImageProcessor(QObject):
    """
    Worker xử lý ảnh gốc cho panel TRÁI.
    Không apply command, chỉ hiển thị ảnh gốc.
    """
    result_signal = Signal(QImage)

    @Slot(bytes)
    def process_original(self, image_blob: bytes):
        """
        Xử lý ảnh gốc đơn giản - không apply command.
        Chỉ chuyển đổi blob → QImage.
        """
        try:
            with WandImage(blob=image_blob) as img:
                # Chỉ chuyển sang QImage, không làm gì thêm
                pixel_data = img.make_blob(format='RGBA')
                qimg = QImage(
                    pixel_data,
                    img.width,
                    img.height,
                    QImage.Format_RGBA8888
                ).copy()
                
                self.result_signal.emit(qimg)
                
        except Exception as e:
            print(f"[OriginalWorker] Error: {e}")

# === Preview Image Processor (Thread 2) ===
class PreviewImageProcessor(QObject):
    """
    Worker xử lý preview cho panel PHẢI.
    Apply command và có queue management.
    """
    result_signal = Signal(PreviewResult)

    def __init__(self):
        super().__init__()
        self._is_busy = False
        self._pending_request = None

    @Slot(object)
    def process_request(self, request: PreviewRequest):
        """
        Nhận request từ UI thread.
        Nếu đang bận, lưu request mới nhất (ghi đè cái cũ).
        """
        if self._is_busy:
            self._pending_request = request
            return

        self._execute(request)

    def _execute(self, request: PreviewRequest):
        """
        Xử lý request với vòng lặp.
        Tránh stack overflow khi user gõ phím liên tục.
        """
        current_req = request
        
        while current_req:
            self._is_busy = True
            
            try:
                # Xử lý ảnh với command
                qimg = self._process_image(current_req)
                
                # Gửi kết quả về UI
                self.result_signal.emit(
                    PreviewResult(current_req.request_id, qimage=qimg)
                )

            except Exception as e:
                self.result_signal.emit(
                    PreviewResult(current_req.request_id, error=str(e))
                )
            
            finally:
                self._is_busy = False
                
                # Lấy request tiếp theo (nếu có)
                current_req = self._pending_request
                self._pending_request = None

    def _process_image(self, request: PreviewRequest) -> QImage:
        """Xử lý ảnh với ImageMagick command"""
        with WandImage(blob=request.image_blob) as img:
            if request.command_string:
                operations = CommandParser.parse(request.command_string)
                CommandParser.apply_commands(img, operations)
            
            # Direct QImage Output
            pixel_data = img.make_blob(format='RGBA')
            qimg = QImage(
                pixel_data,
                img.width,
                img.height,
                QImage.Format_RGBA8888
            ).copy()
            
            return qimg

# === Dual Worker Controller (UI Thread) ===
class PreviewController(QObject):
    """
    Controller quản lý 2 worker độc lập:
    - OriginalWorker: Xử lý ảnh gốc (panel trái)
    - PreviewWorker: Xử lý preview (panel phải)
    """
    # Signals riêng biệt cho 2 panel
    original_ready_signal = Signal(QImage)   # → Panel trái
    preview_ready_signal = Signal(QImage)    # → Panel phải
    
    # Signal gửi request
    original_request_signal = Signal(bytes)
    preview_request_signal = Signal(PreviewRequest)

    def __init__(self):
        super().__init__()
        
        # === THREAD 1: Original Image Worker ===
        self.original_thread = QThread()
        self.original_worker = OriginalImageProcessor()
        self.original_worker.moveToThread(self.original_thread)
        
        # Kết nối signals cho Original Worker
        self.original_request_signal.connect(self.original_worker.process_original)
        self.original_worker.result_signal.connect(self._handle_original_result)
        
        # Khởi động thread 1
        self.original_thread.start()
        
        # === THREAD 2: Preview Worker ===
        self.preview_thread = QThread()
        self.preview_worker = PreviewImageProcessor()
        self.preview_worker.moveToThread(self.preview_thread)
        
        # Kết nối signals cho Preview Worker
        self.preview_request_signal.connect(self.preview_worker.process_request)
        self.preview_worker.result_signal.connect(self._handle_preview_result)
        
        # Quản lý ID cho preview
        self._req_counter = 0
        
        # Khởi động thread 2
        self.preview_thread.start()

    def request_original(self, image_blob: bytes):
        """
        Yêu cầu xử lý ảnh gốc (panel trái).
        Gọi khi load ảnh mới hoặc bật split view.
        """
        if not image_blob:
            return
        
        # Gửi trực tiếp blob, không cần ID
        self.original_request_signal.emit(image_blob)

    def request_preview(self, image_blob: bytes, command_string: str):
        """
        Yêu cầu xử lý preview (panel phải).
        Gọi khi user gõ lệnh hoặc thay đổi command.
        """
        if not image_blob:
            return

        # Tăng ID để tracking
        self._req_counter += 1
        req = PreviewRequest(self._req_counter, image_blob, command_string)
        self.preview_request_signal.emit(req)

    def _handle_original_result(self, qimage: QImage):
        """
        Nhận kết quả từ Original Worker.
        Emit trực tiếp, không cần check ID.
        """
        self.original_ready_signal.emit(qimage)

    def _handle_preview_result(self, result: PreviewResult):
        """
        Nhận kết quả từ Preview Worker.
        Chỉ chấp nhận kết quả mới nhất (check ID).
        """
        # QUAN TRỌNG: Chỉ chấp nhận kết quả mới nhất
        if result.request_id < self._req_counter:
            return  # Vứt bỏ kết quả cũ

        if result.error:
            print(f"Preview Error: {result.error}")
        elif result.qimage:
            self.preview_ready_signal.emit(result.qimage)
    
    def shutdown(self):
        """Dọn dẹp cả 2 threads khi tắt app"""
        # Dừng thread 1
        self.original_thread.quit()
        self.original_thread.wait()
        
        # Dừng thread 2
        self.preview_thread.quit()
        self.preview_thread.wait()