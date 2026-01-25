import os
from pathlib import Path
from typing import Dict, List
from qtpy.QtCore import QThread, Signal
from wand.image import Image as WandImage
from wand.exceptions import BlobError, CorruptImageError, MissingDelegateError

from config import CONFIG
from core.parser import CommandParser

# ========================
# Batch Processor Worker
# ========================
class BatchWorker(QThread):
    """
    Worker xử lý hàng loạt ảnh.
    """
    progress_signal = Signal(int, int, str)
    finished_signal = Signal()
    error_signal = Signal(str)
    log_signal = Signal(str)
    
    def __init__(self, file_structure: Dict[str, List[str]], 
                 input_dir: Path, output_dir: Path, command_string: str,
                 overwrite_mode: str = "overwrite"):
        super().__init__()
        self.file_structure = file_structure
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.command_string = command_string
        self.overwrite_mode = overwrite_mode
        self.is_running = True
        self.processed_count = 0
        self.skipped_count = 0
        self.target_format = self._extract_format_from_command(command_string)
    
    @staticmethod
    def scan_for_conflicts(file_structure: Dict[str, List[str]], 
                          input_dir: Path, output_dir: Path, 
                          command_string: str) -> tuple:
        """
        Quét nhanh xem có file nào bị trùng trong output folder không.
        
        Returns:
            (has_conflicts: bool, conflict_files: List[str])
        """
        conflicts = []
        target_format = BatchWorker._extract_format_from_command_static(command_string)
        
        for rel_path, file_list in file_structure.items():
            output_subfolder = output_dir / rel_path if rel_path else output_dir
            
            for filename in file_list:
                input_path = input_dir / rel_path / filename if rel_path else input_dir / filename
                out_path, _ = BatchWorker._get_output_path_static(
                    input_path, output_subfolder, target_format
                )
                
                if out_path.exists():
                    conflicts.append(str(out_path.name))
        
        return (len(conflicts) > 0, conflicts)

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
        
        self.finished_signal.emit()
    
    def _process_file(self, rel_path, filename, output_subfolder, 
                     operations, file_index, total):
        """Xử lý một file ảnh với mmap và atomic write"""
        input_path = self._get_input_path(rel_path, filename)
        out_path, out_filename = self._get_output_path(input_path, output_subfolder)
        
        log_prefix = f"[{file_index+1}/{total}] {input_path.name}"
        if self.overwrite_mode == "skip" and out_path.exists():
            self.skipped_count += 1
            self.progress_signal.emit(file_index + 1, total, str(input_path))
            self.log_signal.emit(f"{log_prefix} ... ⏭️ SKIPPED (already exists)")
            return
        input_path_str = str(input_path)
        
        try:
            # === BƯỚC 1: VALIDATION VỚI PING ===
            with WandImage(filename=input_path_str) as ping_img:
                # Ping chỉ đọc header, không load full ảnh
                width, height = ping_img.width, ping_img.height
                if width <= 1 or height <= 1:
                    self.skipped_count += 1
                    self.log_signal.emit(f"{log_prefix} ... ✖ INVALID SIZE (1x1)")
                    return
            
            # === BƯỚC 2: XỬ LÝ CHÍNH VỚI MMAP ===
            with WandImage(filename=input_path_str) as img:
                # Áp dụng lệnh
                CommandParser.apply_commands(img, operations)
                output_format = img.format or input_path.suffix.lstrip('.').upper()
                
                # === BƯỚC 3: GHI AN TOÀN VỚI ATOMIC WRITE ===
                temp_output = out_path.with_suffix(out_path.suffix + '.tmp')
                
                try:
                    # Ghi vào file .tmp
                    img.save(filename=str(temp_output))
                except Exception as save_error:
                    # Xóa .tmp nếu ghi thất bại
                    if temp_output.exists():
                        temp_output.unlink()
                    raise save_error
            
            # === BƯỚC 4: ATOMIC REPLACE ===
            if temp_output.exists():
                # os.replace() là atomic operation
                os.replace(str(temp_output), str(out_path))
                
                # Log success
                size_kb = out_path.stat().st_size / 1024
                self.processed_count += 1
                self.progress_signal.emit(file_index + 1, total, str(input_path))
                self.log_signal.emit(f"{log_prefix} -> {out_filename} ({size_kb:.1f} KB) ... ✓ OK")
            else:
                raise FileNotFoundError("Temp file not created")
                
        except (BlobError, CorruptImageError):
            self.skipped_count += 1
            self.log_signal.emit(f"{log_prefix} ... ✖ CORRUPT FILE")
            
        except MissingDelegateError:
            self.skipped_count += 1
            self.log_signal.emit(f"{log_prefix} ... ✖ UNSUPPORTED FORMAT")
            
        except FileNotFoundError:
            self.skipped_count += 1
            self.log_signal.emit(f"{log_prefix} ... ✖ FILE NOT FOUND")
            
        except PermissionError:
            self.skipped_count += 1
            self.log_signal.emit(f"{log_prefix} ... ✖ PERMISSION DENIED")
            
        except Exception as e:
            self.skipped_count += 1
            self.log_signal.emit(f"{log_prefix} ... ✖ ERROR: {str(e)}")
    
    def stop(self):
        """Dừng processing"""
        self.is_running = False
    
    # === Helper Methods ===
    @staticmethod
    def _extract_format_from_command_static(cmd_string):
        """Trích xuất format từ command - STATIC VERSION"""
        operations = CommandParser.parse(cmd_string)
        for cmd, value in operations:
            if cmd == 'format' and value:
                fmt = value.lower().strip()
                return 'jpeg' if fmt == 'jpg' else ('tiff' if fmt == 'tif' else fmt)
        return None

    def _extract_format_from_command(self, cmd_string):
        """Wrapper cho compatibility"""
        return BatchWorker._extract_format_from_command_static(cmd_string)
    
    def _log_start(self, total):
        """Log thông tin bắt đầu"""
        self.log_signal.emit(f"Bắt đầu xử lý {total} file...")
        self.log_signal.emit(f"Lệnh: {self.command_string}")
        
        if self.target_format:
            self.log_signal.emit(f"📋 Định dạng output: .{self.target_format}\n")
        else:
            self.log_signal.emit("📋 Định dạng output: Giữ nguyên\n")
    
    def _log_finish(self, total):
        """Log thống kê cuối cùng"""
        success_rate = (self.processed_count / total * 100) if total > 0 else 0
        
        self.log_signal.emit(f"\n{'='*50}")
        self.log_signal.emit(f"✓ Hoàn thành: {self.processed_count}/{total} file ({success_rate:.1f}%)")
        
        if self.skipped_count > 0:
            self.log_signal.emit(f"⚠ Bỏ qua: {self.skipped_count} file (corrupt/invalid/unsupported)")
        
        self.log_signal.emit(f"{'='*50}")
    
    def _get_output_folder(self, rel_path):
        """Tạo output folder giữ nguyên cấu trúc"""
        output_subfolder = self.output_dir / rel_path if rel_path else self.output_dir
        output_subfolder.mkdir(parents=True, exist_ok=True)
        return output_subfolder
    
    def _get_input_path(self, rel_path, filename):
        """Lấy đường dẫn input"""
        return self.input_dir / rel_path / filename if rel_path else self.input_dir / filename
    
    @staticmethod
    def _get_output_path_static(input_path: Path, output_subfolder: Path, 
                            target_format: str):
        """Xác định tên file output - STATIC VERSION"""
        stem = input_path.stem
        
        if target_format:
            ext_map = {'jpeg': '.jpg', 'tiff': '.tif'}
            new_ext = ext_map.get(target_format, f'.{target_format}')
            out_filename = f"{stem}{new_ext}"
        else:
            out_filename = input_path.name
        
        out_path = output_subfolder / out_filename
        
        # Tránh ghi đè nếu input == output
        if input_path == out_path:
            out_filename = f"{stem}_processed{out_path.suffix}"
            out_path = output_subfolder / out_filename
        
        return out_path, out_filename

    def _get_output_path(self, input_path, output_subfolder):
        """Wrapper cho compatibility"""
        return BatchWorker._get_output_path_static(
            input_path, output_subfolder, self.target_format
        )