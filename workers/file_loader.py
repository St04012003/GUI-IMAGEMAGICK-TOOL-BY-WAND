import re
from pathlib import Path
from typing import Tuple
from PyQt5.QtCore import QThread, pyqtSignal

# ====================
# File Loader Worker
# ====================
class FileLoaderWorker(QThread):
    """
    Worker quét file trong folder và sắp xếp tự nhiên.
    """
    finished_signal = pyqtSignal(dict, list, int)

    def __init__(self, input_path: Path, extensions: Tuple[str, ...], is_folder: bool = True):
        super().__init__()
        self.input_path = input_path
        self.extensions = extensions
        self.is_folder = is_folder

    def run(self):
        """Quét file với hỗ trợ Unicode và Natural Sort"""
        file_structure = {}
        temp_list = []
        
        try:
            if self.is_folder:
                # Quét tất cả file với Natural Sort
                for file_path in sorted(self.input_path.rglob('*'), key=self._natural_key):
                    if not file_path.is_file():
                        continue
                    
                    if not file_path.suffix.lower() in self.extensions:
                        continue
                    
                    try:
                        self._add_to_structure(file_path, file_structure, temp_list)
                    except ValueError:
                        continue
                
                # Sắp xếp lại từng folder
                for key in file_structure:
                    file_structure[key].sort(key=self._natural_key)
                
                flat_file_list = sorted(temp_list, key=self._natural_key)
            else:
                flat_file_list = []

        except Exception as e:
            print(f"Error scanning files: {e}")
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

    @staticmethod
    def _natural_key(text):
        """
        Natural Sort Key Generator.
        Chuyển "file10.jpg" thành ["file", 10, ".jpg"]
        """
        return [int(c) if c.isdigit() else c.lower() 
                for c in re.split(r'(\d+)', str(text))]