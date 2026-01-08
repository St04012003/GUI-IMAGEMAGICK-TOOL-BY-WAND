# workers.py

import gc
import re
from pathlib import Path
from typing import Dict, List, Tuple
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot
from wand.image import Image as WandImage

from config import CONFIG
from core import CommandParser


# ===================================
# WORKER THREADS (BACKGROUND TASKS)
# ===================================
class BatchWorker(QThread):
    """
    Worker xử lý hàng loạt (Batch Processing).
    Chạy khi bấm nút 'START BATCH'.
    """
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, file_structure: Dict[str, List[str]], input_dir: Path, output_dir: Path, command_string: str):
        super().__init__()
        self.file_structure = file_structure  # {rel_path: [files]}
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.command_string = command_string
        self.is_running = True
        self.processed_count = 0        
        self.target_format = self._extract_format_from_command(command_string) # ✅ Phát hiện format từ command
    
    def _extract_format_from_command(self, cmd_string):
        """
        Trích xuất format từ command string
        VD: "-resize 50% -format png" -> "png"
        """
        operations = CommandParser.parse(cmd_string)
        for cmd, value in operations:
            if cmd == 'format' and value:
                fmt = value.lower().strip()
                # Map alias
                if fmt == 'jpg':
                    return 'jpeg'
                elif fmt == 'tif':
                    return 'tiff'
                return fmt
        return None
    
    def run(self):
        operations = CommandParser.parse(self.command_string)
        total = sum(len(files) for files in self.file_structure.values())
        
        self.log_signal.emit(f"Bắt đầu xử lý {total} file...")
        self.log_signal.emit(f"Lệnh: {self.command_string}")
        
        if self.target_format:
            self.log_signal.emit(f"📋 Định dạng output: .{self.target_format}\n")
        else:
            self.log_signal.emit("📋 Định dạng output: Giữ nguyên\n")
            
        file_index = 0
        
        for rel_path, file_list in self.file_structure.items():
            if not self.is_running: 
                break

            # Create output subfolder maintaining relative structure
            output_subfolder = self.output_dir / rel_path if rel_path else self.output_dir
            output_subfolder.mkdir(parents=True, exist_ok=True)
            
            for filename in file_list:
                if not self.is_running:
                    self.log_signal.emit("\n⚠️ Đã dừng xử lý!")
                    break
                
                self._process_file(rel_path, filename, output_subfolder, operations, file_index, total)
                file_index += 1
        
        if self.is_running:
            self.log_signal.emit(f"\n✓ Hoàn thành xử lý {total} file!")
        
        gc.collect()
        self.finished_signal.emit()
    
    def _process_file(self, rel_path, filename, output_subfolder, operations, file_index, total):
        """Process file với hỗ trợ -format"""
        
        input_path = self.input_dir / rel_path / filename if rel_path else self.input_dir / filename
        
        # ✅ XÁC ĐỊNH TÊN FILE OUTPUT
        stem = input_path.stem
        
        # Nếu có -format, thay đổi extension
        if self.target_format:
            # Map format -> extension
            ext_map = {
                'jpeg': '.jpg',
                'tiff': '.tif',
            }
            new_ext = ext_map.get(self.target_format, f'.{self.target_format}')
            out_filename = f"{stem}{new_ext}"
        else:
            # Giữ nguyên extension
            out_filename = filename
        
        # Tránh ghi đè nếu input == output
        out_path = output_subfolder / out_filename
        if input_path == out_path:
            out_filename = f"{stem}_processed{out_path.suffix}"
            out_path = output_subfolder / out_filename
        
        log_prefix = f"[{file_index+1}/{total}] {input_path.name}"

        img_blob = None
        output_blob = None
        
        try:
            # Đọc
            with open(input_path, 'rb') as f:
                img_blob = f.read()
            
            # Xử lý
            with WandImage(blob=img_blob) as img:
                CommandParser.apply_commands(img, operations)
                
                # ✅ XÁC ĐỊNH FORMAT GHI FILE
                # Ưu tiên: img.format (đã set bởi -format) > format gốc
                output_format = img.format or input_path.suffix.lstrip('.').upper()
                
                output_blob = img.make_blob(format=output_format)
            
            # Ghi
            with open(out_path, 'wb') as f:
                f.write(output_blob)
            
            self.processed_count += 1
            
            # Update UI
            self.progress_signal.emit(file_index + 1, total, str(input_path))
            
            # ✅ LOG CHI TIẾT HƠN
            size_kb = len(output_blob) / 1024
            self.log_signal.emit(f"{log_prefix} -> {out_filename} ({size_kb:.1f} KB) ... ✓ OK")
            
            if self.processed_count % CONFIG.gc_interval == 0:
                gc.collect()
            
        except Exception as e:
            self.log_signal.emit(f"{log_prefix} ... ✖ ERROR: {str(e)}")
        
        finally:
            # ✅ FIX: Cleanup memory
            img_blob = None
            output_blob = None
    
    def stop(self):
        self.is_running = False


class FileLoaderWorker(QThread):
    """
    Worker chuyên dụng quét file với thuật toán NATURAL SORT.
    Giúp sắp xếp đúng số tự nhiên: 1, 2, 10... thay vì 1, 10, 2...
    """
    finished_signal = pyqtSignal(dict, list, int) # structure, flat_list, total_count

    def __init__(self, input_path: Path, extensions: Tuple[str, ...], is_folder: bool = True):
        super().__init__()
        self.input_path = input_path
        self.extensions = extensions
        self.is_folder = is_folder

    def run(self):
        """File scanner with FIXED Unicode support"""
        file_structure = {}
        temp_list = []
        
        def natural_key(text):
            return [int(c) if c.isdigit() else c.lower() 
                    for c in re.split(r'(\d+)', str(text))]

        try:
            if self.is_folder:
                # ✅ FIX: Dùng pathlib thay vì os.walk (hỗ trợ Unicode tốt hơn)
                for file_path in sorted(self.input_path.rglob('*'), key=natural_key):
                    # Chỉ xử lý file (không phải folder)
                    if not file_path.is_file():
                        continue
                    
                    # Lọc đuôi ảnh
                    if not file_path.suffix.lower() in self.extensions:
                        continue
                    
                    try:
                        # Tính relative path
                        rel_path = file_path.relative_to(self.input_path).parent
                        rel_path_str = str(rel_path) if rel_path != Path('.') else ""
                        
                        # Thêm vào structure
                        if rel_path_str not in file_structure:
                            file_structure[rel_path_str] = []
                        
                        file_structure[rel_path_str].append(file_path.name)
                        
                        # Thêm vào flat list
                        full_rel_path = Path(rel_path_str) / file_path.name if rel_path_str else Path(file_path.name)
                        temp_list.append(str(full_rel_path))
                        
                    except ValueError:
                        # Skip nếu không tính được relative path
                        continue
                
                # Sắp xếp lại từng folder
                for key in file_structure:
                    file_structure[key].sort(key=natural_key)
                
                # Sắp xếp flat list
                flat_file_list = sorted(temp_list, key=natural_key)
            else:
                flat_file_list = []

        except Exception as e:
            print(f"Error scanning files: {e}")
            flat_file_list = []

        self.finished_signal.emit(file_structure, flat_file_list, len(flat_file_list))

# ==========================================================
# 5. NEW THREADING ARCHITECTURE (Long-lived Worker)
# ==========================================================

class PreviewRequest:
    """Gói dữ liệu yêu cầu xử lý"""
    def __init__(self, request_id, image_blob, command_string):
        self.request_id = request_id
        self.image_blob = image_blob
        self.command_string = command_string

class PreviewResult:
    """Gói dữ liệu kết quả trả về"""
    def __init__(self, request_id, image_blob=None, error=None):
        self.request_id = request_id
        self.image_blob = image_blob
        self.error = error

class AsyncTaskProcessor(QObject):
    """
    Worker xử lý ảnh chạy trên một Thread riêng biệt vĩnh viễn.
    Sử dụng tín hiệu để giao tiếp, không bao giờ bị kill đột ngột.
    """
    result_signal = pyqtSignal(PreviewResult)

    def __init__(self):
        super().__init__()
        self._current_request = None
        self._is_busy = False
        self._pending_request = None # Lưu yêu cầu mới nhất nếu đang bận

    @pyqtSlot(PreviewRequest)
    def process_request(self, request: PreviewRequest):
        # Nếu đang bận, lưu vào hàng chờ (chỉ giữ cái mới nhất, ghi đè cái cũ)
        if self._is_busy:
            self._pending_request = request
            return

        self._execute(request)

    def _execute(self, request: PreviewRequest):
        """Xử lý request với vòng lặp thay vì đệ quy"""
        current_req = request
        
        while current_req:
            self._is_busy = True
            self._current_request = current_req
            
            try:
                # --- XỬ LÝ ẢNH (Nặng) ---
                out_blob = None
                
                with WandImage(blob=current_req.image_blob) as img:
                    if current_req.command_string:
                        operations = CommandParser.parse(current_req.command_string)
                        CommandParser.apply_commands(img, operations)
                    
                    out_blob = img.make_blob(format='bmp')

                # Gửi kết quả về
                self.result_signal.emit(PreviewResult(current_req.request_id, image_blob=out_blob))

            except Exception as e:
                self.result_signal.emit(PreviewResult(current_req.request_id, error=str(e)))
            
            finally:
                self._is_busy = False
                
                # ✅ Lấy request tiếp theo (nếu có) và tiếp tục vòng lặp
                current_req = self._pending_request
                self._pending_request = None

class PreviewController(QObject):
    """
    Controller nằm ở UI Thread, quản lý việc gửi request.
    Đảm bảo ID request luôn tăng dần để UI không hiển thị kết quả cũ.
    """
    request_signal = pyqtSignal(PreviewRequest) # Gửi đi cho Worker
    preview_ready_signal = pyqtSignal(bytes)    # Gửi blob ảnh về cho UI chính

    def __init__(self):
        super().__init__()
        self.worker_thread = QThread()
        self.worker = AsyncTaskProcessor()
        
        # Di chuyển worker vào thread
        self.worker.moveToThread(self.worker_thread)
        
        # Kết nối tín hiệu
        self.request_signal.connect(self.worker.process_request)
        self.worker.result_signal.connect(self._handle_result)
        
        # Quản lý ID
        self._req_counter = 0
        self._last_completed_id = 0
        
        # Khởi động thread
        self.worker_thread.start()

    def request_preview(self, image_blob, command_string):
        """UI gọi hàm này để yêu cầu preview"""
        if not image_blob: 
            return

        self._req_counter += 1
        req = PreviewRequest(self._req_counter, image_blob, command_string)
        self.request_signal.emit(req)

    def _handle_result(self, result: PreviewResult):
        """Nhận kết quả từ Worker"""
        # QUAN TRỌNG: Chỉ chấp nhận kết quả mới nhất hoặc mới hơn cái đang hiển thị
        if result.request_id < self._req_counter:
            # Đây là kết quả của một lệnh cũ (do gõ phím quá nhanh), vứt bỏ.
            # print(f"Dropped stale result {result.request_id} (Current: {self._req_counter})")
            return

        if result.error:
            print(f"Preview Error: {result.error}")
        elif result.image_blob:
            self.preview_ready_signal.emit(result.image_blob)
    
    def shutdown(self):
        """Dọn dẹp sạch sẽ khi tắt app"""
        self.worker_thread.quit()
        self.worker_thread.wait()