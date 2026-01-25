import re
import os
import unicodedata
from pathlib import Path
from typing import Tuple
from qtpy.QtCore import QThread, Signal
from qtpy.QtWidgets import QMessageBox

# ====================
# File Loader Worker
# ====================
class FileLoaderWorker(QThread):
    """
    Worker quét file trong folder và sắp xếp tự nhiên.
    """
    finished_signal = Signal(dict, list, int)
    error_signal = Signal(str)

    def __init__(self, input_path: Path, extensions: Tuple[str, ...], is_folder: bool = True):
        super().__init__()
        self.input_path = input_path
        self.extensions = extensions
        self.is_folder = is_folder

    @staticmethod
    def _natural_key(text):
        """
        Tạo key sắp xếp tự nhiên:
        1. Chuẩn hóa Unicode (NFC) -> Sắp xếp đúng tiếng Việt (a < á < b).
        2. Tách số ra khỏi chữ -> Sắp xếp đúng số học (img1 < img2 < img10).
        """
        text = str(text)
        # Chuẩn hóa về NFC để các ký tự tiếng Việt có dấu được xử lý đồng nhất
        text = unicodedata.normalize('NFC', text.lower())
        
        # Tách chuỗi thành list gồm chuỗi và số: "img10" -> ['img', 10, '']
        return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]
    
    def run(self):
        """Quét file với hỗ trợ Unicode và Natural Sort"""
        
        # VALIDATION Ổ C:
        if self.input_path.drive.upper() == 'C:' and self.input_path == Path('C:/'):
            self.error_signal.emit("⚠️ Không thể quét toàn bộ ổ C:\nVui lòng chọn thư mục cụ thể!")
            return
    
        file_structure = {}
        temp_list = []
        
        try:
            if self.is_folder:
                # SỬ DỤNG os.scandir() thay cho rglob
                def scan_directory(path: Path):
                    """Quét đệ quy bằng os.scandir (nhanh hơn rglob)"""
                    try:
                        with os.scandir(path) as entries:
                            for entry in entries:
                                if entry.is_file(follow_symlinks=False):
                                    file_path = Path(entry.path)
                                    if file_path.suffix.lower() in self.extensions:
                                        try:
                                            self._add_to_structure(file_path, file_structure, temp_list)
                                        except ValueError:
                                            continue
                                elif entry.is_dir(follow_symlinks=False):
                                    # Đệ quy vào subfolder
                                    scan_directory(Path(entry.path))
                    except PermissionError:
                        # Bỏ qua folder không có quyền truy cập
                        pass
                    except OSError:
                        # Bỏ qua lỗi hệ thống (symlink lỗi, etc.)
                        pass
                
                # Bắt đầu quét
                scan_directory(self.input_path)
                
                # Sắp xếp lại từng folder
                for key in file_structure:
                    file_structure[key].sort(key=self._natural_key)
                
                flat_file_list = sorted(temp_list, key=self._natural_key)
            else:
                flat_file_list = []

        except Exception as e:
            self.error_signal.emit(f"Lỗi quét file: {str(e)}")
            flat_file_list = []

        self.finished_signal.emit(file_structure, flat_file_list, len(flat_file_list))

    def _add_to_structure(self, file_path: Path, structure: dict, temp_list: list):
        """Thêm file vào cấu trúc dữ liệu"""
        rel_path = file_path.relative_to(self.input_path).parent
        rel_path_str = str(rel_path) if rel_path != Path('.') else ""
        
        if rel_path_str not in structure:
            structure[rel_path_str] = []
        
        structure[rel_path_str].append(file_path.name)
        
        full_rel_path = Path(rel_path_str) / file_path.name if rel_path_str else Path(file_path.name)
        temp_list.append(str(full_rel_path))

    