import gc
from pathlib import Path
from typing import Dict, List
from PyQt5.QtCore import QThread, pyqtSignal
from wand.image import Image as WandImage

from config import CONFIG
from core import CommandParser

# ========================
# Batch Processor Worker
# ========================
class BatchWorker(QThread):
    """
    Worker xử lý hàng loạt ảnh.
    """
    progress_signal = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, file_structure: Dict[str, List[str]], 
                 input_dir: Path, output_dir: Path, command_string: str):
        super().__init__()
        self.file_structure = file_structure
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.command_string = command_string
        self.is_running = True
        self.processed_count = 0
        self.target_format = self._extract_format_from_command(command_string)
    
    def run(self):
        """Main processing loop"""
        operations = CommandParser.parse(self.command_string)
        total = sum(len(files) for files in self.file_structure.values())
        
        self._log_start(total)
        
        file_index = 0
        for rel_path, file_list in self.file_structure.items():
            if not self.is_running: 
                break

            output_subfolder = self._get_output_folder(rel_path)
            
            for filename in file_list:
                if not self.is_running:
                    self.log_signal.emit("\n⚠️ Đã dừng xử lý!")
                    break
                
                self._process_file(rel_path, filename, output_subfolder, 
                                 operations, file_index, total)
                file_index += 1
        
        if self.is_running:
            self.log_signal.emit(f"\n✓ Hoàn thành xử lý {total} file!")
        
        gc.collect()
        self.finished_signal.emit()
    
    def _process_file(self, rel_path, filename, output_subfolder, 
                     operations, file_index, total):
        """Xử lý một file ảnh"""
        input_path = self._get_input_path(rel_path, filename)
        out_path, out_filename = self._get_output_path(input_path, output_subfolder)
        
        log_prefix = f"[{file_index+1}/{total}] {input_path.name}"
        
        try:
            # Đọc file
            with open(input_path, 'rb') as f:
                img_blob = f.read()
            
            # Xử lý
            with WandImage(blob=img_blob) as img:
                CommandParser.apply_commands(img, operations)
                output_format = img.format or input_path.suffix.lstrip('.').upper()
                output_blob = img.make_blob(format=output_format)
            
            # Ghi file
            with open(out_path, 'wb') as f:
                f.write(output_blob)
            
            self.processed_count += 1
            self.progress_signal.emit(file_index + 1, total, str(input_path))
            
            size_kb = len(output_blob) / 1024
            self.log_signal.emit(f"{log_prefix} -> {out_filename} ({size_kb:.1f} KB) ... ✓ OK")
            
            if self.processed_count % CONFIG.gc_interval == 0:
                gc.collect()
            
        except Exception as e:
            self.log_signal.emit(f"{log_prefix} ... ✖ ERROR: {str(e)}")
    
    def stop(self):
        """Dừng processing"""
        self.is_running = False
    
    # === Helper Methods ===
    
    def _extract_format_from_command(self, cmd_string):
        """Trích xuất format từ command (VD: '-format png' -> 'png')"""
        operations = CommandParser.parse(cmd_string)
        for cmd, value in operations:
            if cmd == 'format' and value:
                fmt = value.lower().strip()
                return 'jpeg' if fmt == 'jpg' else ('tiff' if fmt == 'tif' else fmt)
        return None
    
    def _log_start(self, total):
        """Log thông tin bắt đầu"""
        self.log_signal.emit(f"Bắt đầu xử lý {total} file...")
        self.log_signal.emit(f"Lệnh: {self.command_string}")
        
        if self.target_format:
            self.log_signal.emit(f"📋 Định dạng output: .{self.target_format}\n")
        else:
            self.log_signal.emit("📋 Định dạng output: Giữ nguyên\n")
    
    def _get_output_folder(self, rel_path):
        """Tạo output folder giữ nguyên cấu trúc"""
        output_subfolder = self.output_dir / rel_path if rel_path else self.output_dir
        output_subfolder.mkdir(parents=True, exist_ok=True)
        return output_subfolder
    
    def _get_input_path(self, rel_path, filename):
        """Lấy đường dẫn input"""
        return self.input_dir / rel_path / filename if rel_path else self.input_dir / filename
    
    def _get_output_path(self, input_path, output_subfolder):
        """Xác định tên file output"""
        stem = input_path.stem
        
        if self.target_format:
            ext_map = {'jpeg': '.jpg', 'tiff': '.tif'}
            new_ext = ext_map.get(self.target_format, f'.{self.target_format}')
            out_filename = f"{stem}{new_ext}"
        else:
            out_filename = input_path.name
        
        out_path = output_subfolder / out_filename
        
        # Tránh ghi đè nếu input == output
        if input_path == out_path:
            out_filename = f"{stem}_processed{out_path.suffix}"
            out_path = output_subfolder / out_filename
        
        return out_path, out_filename