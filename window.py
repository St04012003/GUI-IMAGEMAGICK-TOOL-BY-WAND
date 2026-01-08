# 7.window.py
import json
from pathlib import Path
from typing import List, Dict

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel, QListWidget, QProgressBar, QTextEdit, QMessageBox, QFileDialog, QInputDialog, QGridLayout, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QImage, QPixmap
from wand.image import Image as WandImage

from config import CONFIG
from core import ImageCache
from workers import BatchWorker, FileLoaderWorker, PreviewController
from widgets import ImageCanvas, SmartCommandEdit, create_button, create_groupbox
from dialogs import HelpDialog


# ===============
# MAIN WINDOW 
# ===============

class ImageMagickTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ImageMagick GUI Tool {CONFIG.app_version}")
        self.resize(1700, 1000)
        
        self.settings = QSettings(str(CONFIG.settings_file), QSettings.IniFormat)
        
        self.cache = ImageCache(max_size=30)  # Khởi tạo cache chứa 30 lệnh

        # State
        self.input_dir = Path(self.settings.value("last_input_dir", ""))
        self.output_dir = Path(self.settings.value("last_output_dir", ""))
        self.image_files: List[Path] = []
        self.file_structure: Dict[str, List[str]] = {}  # {rel_path: [files]}
        self.current_index = -1
        self.current_command = ""
        self.worker: Optional[BatchWorker] = None
        self.preview_controller = PreviewController()
        self.preview_controller.preview_ready_signal.connect(self._on_preview_ready_thread_safe)
        self.split_view_enabled = False                  
        self.file_loader_worker: Optional[FileLoaderWorker] = None
        self.ui_load_timer = QTimer()
        self.ui_load_timer.setInterval(20) # 20ms mỗi lần nạp UI
        self.ui_load_timer.timeout.connect(self._process_ui_load_queue)
        self.pending_files_queue = [] # Queue chứa file chờ hiển thị

        # Debounce timer
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(CONFIG.debounce_delay)
        self.debounce_timer.timeout.connect(self._execute_preview_update)
        self.preview_pending = False
        self._preview_lock = False

        self._init_ui()
        
        if self.input_dir.exists():
             self.lbl_input.setText(str(self.input_dir))
        
        if self.output_dir.exists():
            self.lbl_output.setText(self.output_dir.name)

    def closeEvent(self, event):
        # 1. Lưu settings
        if self.output_dir:
            self.settings.setValue("last_output_dir", str(self.output_dir))
        
        if self.input_dir and self.input_dir.exists():
            self.settings.setValue("last_input_dir", str(self.input_dir))
        
        # 2. ✅ Dừng preview controller
        if hasattr(self, 'preview_controller'):
            self.preview_controller.shutdown()
        
        # 3. ✅ Dừng batch worker
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.stop()
            if not self.worker.wait(3000):  # Chờ 3s
                print("⚠️ Batch worker timeout, forcing termination")
                self.worker.terminate()
                self.worker.wait()
        
        # 4. ✅ Dừng file loader worker
        if hasattr(self, 'file_loader_worker') and self.file_loader_worker and self.file_loader_worker.isRunning():
            if not self.file_loader_worker.wait(1000):  # Chờ 1s
                self.file_loader_worker.terminate()
                self.file_loader_worker.wait()
        
        # 5. ✅ Dừng UI timer
        if hasattr(self, 'ui_load_timer') and self.ui_load_timer.isActive():
            self.ui_load_timer.stop()
        
        if hasattr(self, 'debounce_timer') and self.debounce_timer.isActive():
            self.debounce_timer.stop()
        
        # 6. ✅ Giải phóng blob cache
        if hasattr(self, 'cached_source_blob'):
            self.cached_source_blob = None
        
        # 7. ✅ Xóa cache
        if hasattr(self, 'cache'):
            self.cache.clear()
        
        event.accept()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self._create_left_column())
        self.main_splitter.addWidget(self._create_middle_column())
        self.main_splitter.addWidget(self._create_right_column())
        self.main_splitter.setSizes([250, 1000, 400])

        main_layout.addWidget(self.main_splitter)

    def _create_left_column(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(self._create_io_group())
        v_splitter.addWidget(self._create_file_list_group())
        v_splitter.addWidget(self._create_presets_group())
        v_splitter.setSizes([120, 300, 300])
        
        layout.addWidget(v_splitter)
        return container
    
    def _create_io_group(self):
        group, layout = create_groupbox("I/O Settings")
        
        self.btn_input = create_button("Input Files/Folder", self._select_input)
        self.lbl_input = QLabel("...")
        self.lbl_input.setWordWrap(True)
        
        self.btn_output = create_button("Output Folder", self._select_output_dir)
        self.lbl_output = QLabel("...")
        
        for w in [self.btn_input, self.lbl_input, self.btn_output, self.lbl_output]:
            layout.addWidget(w)
        
        return group
    
    def _create_file_list_group(self):
        group, layout = create_groupbox("Danh sách File")
        self.list_files = QListWidget()
        self.list_files.currentRowChanged.connect(self._on_file_list_changed)
        layout.addWidget(self.list_files)
        return group
    
    def _create_presets_group(self):
        group, layout = create_groupbox("Presets Manager")
        
        self.list_presets = QListWidget()
        self.list_presets.itemDoubleClicked.connect(self._load_preset_from_item)
        
        # Thêm context menu (chuột phải) để Rename
        self.list_presets.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_presets.customContextMenuRequested.connect(self._show_preset_context_menu)
        
        layout.addWidget(self.list_presets)
        
        # Grid 4 nút: Save, Delete, Import, Export
        btn_grid = QGridLayout()
        buttons = [
            (create_button("Save", self._save_preset, height=30), 0, 0),
            (create_button("Delete", self._delete_preset, height=30), 0, 1),
            (create_button("Import", self._import_presets, height=30), 1, 0),
            (create_button("Export", self._export_presets, height=30), 1, 1),
        ]
        for btn, row, col in buttons:
            btn_grid.addWidget(btn, row, col)
        
        layout.addLayout(btn_grid)
        self._update_presets_list()
        return group
    
    def _show_preset_context_menu(self, position):
        item = self.list_presets.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_preset(item))
        menu.addAction(rename_action)
        menu.exec_(self.list_presets.mapToGlobal(position))

    def _rename_preset(self, item):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Preset", "Tên mới:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if old_name in data:
                    data[new_name] = data[old_name]
                    del data[old_name]
                    
                    with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    self._update_presets_list()

    def _import_presets(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Presets", "", "JSON (*.json)")
        if not path:
            return

        try:
            # 1. Đọc file mới
            with open(path, 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            # Validate
            if not isinstance(new_data, dict):
                raise ValueError("File JSON phải là Dictionary")
            
            valid_new_data = {k: v for k, v in new_data.items() if isinstance(k, str) and isinstance(v, str)}
            
            # 2. Đọc dữ liệu cũ
            current_data = {}
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    try: current_data = json.load(f)
                    except: current_data = {}

            # 3. Kiểm tra trùng lặp
            conflicts = [k for k in valid_new_data.keys() if k in current_data]
            
            if conflicts:
                # --- LẤY ƯU ĐIỂM CỦA CODE 2: Liệt kê danh sách ---
                conflict_list = "\n".join(f" - {name}" for name in conflicts[:5])
                if len(conflicts) > 5:
                    conflict_list += f"\n ... và {len(conflicts) - 5} preset khác."

                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Xung đột dữ liệu")
                msg.setText(f"Có {len(conflicts)} preset đã tồn tại trong máy:")
                msg.setInformativeText(f"{conflict_list}\n\nBạn muốn xử lý thế nào?")
                
                # --- LẤY ƯU ĐIỂM CỦA CODE 1: Các nút tùy chọn ---
                btn_overwrite = msg.addButton("Ghi đè tất cả", QMessageBox.ActionRole)
                btn_skip = msg.addButton("Giữ cũ, bỏ qua trùng", QMessageBox.ActionRole)
                btn_cancel = msg.addButton("Hủy Import", QMessageBox.RejectRole)
                
                msg.exec_()
                
                if msg.clickedButton() == btn_cancel:
                    return
                elif msg.clickedButton() == btn_skip:
                    # Loại bỏ các key trùng khỏi danh sách import
                    for k in conflicts:
                        del valid_new_data[k]
                # Nếu chọn btn_overwrite thì không cần làm gì (mặc định sẽ update đè lên)

            # 4. Merge và Lưu
            current_data.update(valid_new_data)
            with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)

            self._update_presets_list()
            QMessageBox.information(self, "Thành công", f"Đã import {len(valid_new_data)} preset!")

        except Exception as e:
            QMessageBox.warning(self, "Lỗi Import", str(e))

    def _export_presets(self):
        if not CONFIG.preset_file.exists():
            QMessageBox.warning(self, "Lỗi", "Không có preset nào để export!")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Presets", 
            "presets_backup.json", 
            "JSON (*.json)"
        )
        if path:
            try:
                # Đọc file gốc
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Ghi sang file mới
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "OK", "Export thành công!")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def _create_middle_column(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container cho split view
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(2)
        
        # Canvas chính (luôn hiển thị)
        self.image_canvas = ImageCanvas(sync_callback=self._sync_from_right)
        
        # Canvas bên trái (cho ảnh gốc khi split view)
        self.image_canvas_left = ImageCanvas(sync_callback=self._sync_from_left)
        self.image_canvas_left.hide()
        
        self.preview_layout.addWidget(self.image_canvas_left)
        self.preview_layout.addWidget(self.image_canvas)
        
        # Navigation + Split View Toggle
        nav_layout = QHBoxLayout()
        self.btn_prev = create_button("◄ Prev", self._prev_image)
        self.btn_next = create_button("Next ►", self._next_image)
        
        # Nút toggle split view
        self.btn_toggle_split = create_button(
            "Split View: OFF", 
            self._toggle_split_view,
            "background-color: #607D8B; color: white; font-weight: bold;",
            35
        )
        
        self.lbl_info = QLabel("No Image")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_info, 1)
        nav_layout.addWidget(self.btn_toggle_split)  # ← NÚT MỚI
        nav_layout.addWidget(self.btn_next)
        
        layout.addWidget(self.preview_container) 
        layout.addLayout(nav_layout)
        return container

    def _create_right_column(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(self._create_batch_group())
        v_splitter.addWidget(self._create_log_group())
        v_splitter.addWidget(self._create_command_group())
        v_splitter.setSizes([120, 200, 200])
        
        layout.addWidget(v_splitter)
        layout.addLayout(self._create_footer())
        return container
    
    def _create_batch_group(self):
        group, layout = create_groupbox("Batch Processing")
        layout.setSpacing(2)  # Consistent spacing
        layout.setContentsMargins(5,5,5,5)
        
        # Chiều cao thống nhất cho tất cả widget để kích thước đều nhau
        WIDGET_HEIGHT = 35

        self.btn_start = create_button(
            "START BATCH",
            self._start_batch_thread,
            "background-color: #4CAF50; color: white; font-weight: bold;",
            WIDGET_HEIGHT
        )
        self.btn_stop = create_button(
            "STOP",
            self._stop_batch_thread,
            "background-color: #F44336; color: white; font-weight: bold;",
            WIDGET_HEIGHT
        )
        self.btn_stop.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(WIDGET_HEIGHT)
        
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        
        for w in [self.btn_start, self.btn_stop, self.progress_bar]:
            layout.addWidget(w)
        
        return group
    
    def _create_log_group(self):
        group, layout = create_groupbox("Progress Log")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #2b2b2b; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.txt_log)
        return group
    
    def _create_command_group(self):
        group, layout = create_groupbox("Command Input")
        self.txt_command = SmartCommandEdit()
        self.txt_command.textChanged.connect(self._on_command_changed)
        self.txt_command.setMinimumHeight(150)
        layout.addWidget(self.txt_command)
        return group
    
    def _create_footer(self):
        footer = QHBoxLayout()
        self.btn_help = create_button(
            "Hướng dẫn",
            self._show_help_dialog,
            "background-color: #008CBA; color: white; font-weight: bold;",
            40
        )
        self.btn_clear = create_button(
            "Clear Command",
            lambda: self.txt_command.clear(),
            "background-color: #ff5722; color: white; font-weight: bold;",
            40
        )
        footer.addWidget(self.btn_help)
        footer.addWidget(self.btn_clear)
        return footer

    # Input/Output handlers
    def _select_input(self):
        start_dir = str(self.input_dir) if self.input_dir.exists() else ""

        msg = QMessageBox()
        msg.setWindowTitle("Chọn Input")
        msg.setText("Bạn muốn chọn:")
        btn_files = msg.addButton("Chọn Files", QMessageBox.ActionRole)
        btn_folder = msg.addButton("Chọn Folder", QMessageBox.ActionRole)
        msg.addButton("Hủy", QMessageBox.RejectRole)
        msg.exec_()
        
        if msg.clickedButton() == btn_files:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Chọn file ảnh", start_dir, # [SỬA] Dùng start_dir
                f"Images ({' '.join(['*' + e for e in CONFIG.image_extensions])})"
            )
            if files:
                self.input_dir = Path(files[0]).parent
                file_names = sorted([Path(f).name for f in files]) # Sort A-Z
                self.file_structure = {"": file_names}
                self.image_files = file_names
                self._finalize_load_files(len(files))
                
        elif msg.clickedButton() == btn_folder:
            d = QFileDialog.getExistingDirectory(self, "Chọn Input Folder", start_dir) # [SỬA] Dùng start_dir
            if d:
                self.input_dir = Path(d)
                self.list_files.clear()
                self.list_files.addItem("Đang quét file... Vui lòng đợi...")
                self.btn_input.setEnabled(False) 
                
                # CHẠY WORKER
                self.file_loader_worker = FileLoaderWorker(self.input_dir, CONFIG.image_extensions)
                self.file_loader_worker.finished_signal.connect(self._on_scan_finished)
                self.file_loader_worker.start()

    def _on_scan_finished(self, structure, flat_list, total_count):
        """Nhận kết quả từ Worker"""
        self.file_structure = structure
        self.image_files = flat_list
        self.btn_input.setEnabled(True)
        
        if total_count == 0:
            self.list_files.clear()
            self.list_files.addItem("(Không tìm thấy ảnh nào)")
            return

        self._finalize_load_files(total_count)

    def _finalize_load_files(self, total_count):
        """Chuẩn bị nạp vào List Widget"""
        self.lbl_input.setText(f"{self.input_dir.name} ({total_count} files)")
        
        # Reset ListWidget
        self.list_files.clear()
        
        # Đưa toàn bộ file vào hàng đợi để nạp từ từ
        self.pending_files_queue = list(self.image_files) 
        
        # Nạp ngay 50 file đầu tiên 
        initial_batch = self.pending_files_queue[:50]
        self.list_files.addItems(initial_batch)
        del self.pending_files_queue[:50] 
        
        # Chọn file đầu tiên ngay lập tức
        if self.image_files:
            self.current_index = 0
            self.list_files.setCurrentRow(0)
            self._load_image_from_file()
            
        # Nếu còn file, bật Timer để nạp tiếp
        if self.pending_files_queue:
            self.ui_load_timer.start()

    def _process_ui_load_queue(self):
        """Hàm được Timer gọi liên tục để nạp file vào ListWidget"""
        if not self.pending_files_queue:
            self.ui_load_timer.stop()
            return

        # Mỗi lần nạp 200 file
        BATCH_SIZE = 200
        batch = self.pending_files_queue[:BATCH_SIZE]
        self.list_files.addItems(batch)
        
        del self.pending_files_queue[:BATCH_SIZE]
    
    
    def _select_output_dir(self):
        start_dir = str(self.output_dir) if self.output_dir.exists() else ""
        d = QFileDialog.getExistingDirectory(self, "Chọn Output Folder", start_dir)
        if d:
            self.output_dir = Path(d)
            self.lbl_output.setText(self.output_dir.name)
    

    def _on_file_list_changed(self, index):
        if 0 <= index < len(self.image_files):
            self.current_index = index
            self._load_image_from_file()
    
    
    def _load_image_from_file(self):    
        """Load image with Crash Prevention logic"""
        if not (0 <= self.current_index < len(self.image_files)):
            return
        
        filepath = self.input_dir / self.image_files[self.current_index]    
        
        # ========================================================
        # 🛑 BƯỚC 1: DỪNG TOÀN BỘ TÁC VỤ CŨ
        # ========================================================        
        self.debounce_timer.stop() 
        self.preview_pending = False        

        # ========================================================
        # 🗑️ BƯỚC 2: DỌN DẸP ẢNH CŨ AN TOÀN
        # ========================================================            
        # Xóa cache cũ
        if hasattr(self, 'cache'):
            self.cache.clear()
        
        # Xóa blob cũ (nếu có)
        if hasattr(self, 'cached_source_blob'):
            self.cached_source_blob = None

        # ========================================================
        # 📂 BƯỚC 3: LOAD ẢNH MỚI
        # ========================================================
        try:
            # 1. Đọc file
            with open(filepath, 'rb') as f:
                img_blob = f.read()
            
            # 2. Tạo preview blob NGOÀI context manager
            temp_blob = None
            
            # ✅ FIX: Dùng try-finally để đảm bảo cleanup
            preview_img = None
            try:
                with WandImage(blob=img_blob) as img:
                    # Clone ra để xử lý (tự động tạo context riêng)
                    preview_img = img.clone()
                
                # ✅ CRITICAL: Xử lý NGOÀI context manager của img gốc
                if preview_img.width > 1200 or preview_img.height > 1200:
                    preview_img.transform(resize="800x1200>")
                
                # Tạo blob
                temp_blob = preview_img.make_blob(format='bmp')
                
            finally:
                # ✅ FIX: Cleanup an toàn trong finally block
                if preview_img is not None:
                    try:
                        preview_img.destroy()  # Tốt hơn close()
                    except:
                        pass
            
            # Gán vào biến instance SAU KHI đã tạo xong
            self.cached_source_blob = temp_blob
                        
            self.lbl_info.setText(f"{self.current_index + 1}/{len(self.image_files)}: {filepath.name}")
            
            # Reset view
            self.image_canvas.reset_view_flag = True 
            
            if self.split_view_enabled:
                self._update_left_canvas_once()

            self._execute_preview_update()
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể đọc ảnh:\n{str(e)}")

    def _prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.list_files.setCurrentRow(self.current_index)

    def _next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.list_files.setCurrentRow(self.current_index)

    # Command handlers
    def _on_command_changed(self):
        self.current_command = self.txt_command.toPlainText().strip()
        self.preview_pending = True
        self.debounce_timer.start()
    
    def _update_left_canvas_once(self):
        """Cập nhật ảnh trái một lần duy nhất (dùng cache blob)"""
        try:
            if hasattr(self, 'cached_source_blob') and self.cached_source_blob:
                left_pixmap = QPixmap.fromImage(QImage.fromData(self.cached_source_blob))
                should_reset = getattr(self.image_canvas, 'reset_view_flag', False)
                self.image_canvas_left.set_image(left_pixmap, reset_view=should_reset)
        except Exception as e:
            print(f"Lỗi hiển thị ảnh trái: {e}")

    def _execute_preview_update(self):
        # 1. CHECK AN TOÀN
        if not hasattr(self, 'cached_source_blob') or self.cached_source_blob is None:
            return

        # ✅ FIX: Thêm lock để tránh duplicate request
        if hasattr(self, '_preview_lock') and self._preview_lock:
            return
    
        try:
            self._preview_lock = True
            # 2. Lấy lệnh hiện tại
            raw_cmd = self.txt_command.toPlainText().strip()
            
            # 3. Reset pending flag
            self.preview_pending = False
            
            # 4. KIỂM TRA CACHE
            cached_img = self.cache.get(raw_cmd)
            if cached_img:
                if self.split_view_enabled:
                    self._update_right_canvas_only(cached_img, is_from_cache=True)
                else:
                    self._display_qimage(cached_img)
                return

            # 5. Gửi request
            self.preview_controller.request_preview(self.cached_source_blob, raw_cmd)
            
        finally:
            # ✅ FIX: Luôn mở lock
            self._preview_lock = False

    def _on_preview_ready_thread_safe(self, blob_data):
        """Callback nhận dữ liệu từ Thread an toàn"""
        try:
            # Convert bytes -> QImage (Nhanh, chạy trên UI thread ok)
            qimg = QImage.fromData(blob_data)
            
            # Logic phân phối y hệt cũ
            if self.split_view_enabled:
                self._update_right_canvas_only(qimg)
            else:
                self._update_preview_display(qimg)
                
        except Exception as e:
            print(f"Error handling preview result: {e}")
            
    def _update_preview_display(self, result):
        """Callback cho chế độ thường"""
        try:
            # Nếu result là QImage (từ Worker BMP) thì dùng luôn
            # Nếu là bytes (phòng hờ) thì convert
            qimg = result if isinstance(result, QImage) else QImage.fromData(result)
            
            # 1. LƯU CACHE
            current_cmd = self.txt_command.toPlainText().strip()
            self.cache.put(current_cmd, qimg)
            
            # 2. HIỂN THỊ
            self._display_qimage(qimg)            
            
        except Exception as e:
            print(f"Display error: {e}")

    def _update_right_canvas_only(self, result, is_from_cache=False):
        """Callback cho chế độ Split View (chỉ update bên phải)"""
        try:
            qimg = result if isinstance(result, QImage) else QImage.fromData(result)
            
            # 1. LƯU CACHE (Nếu chưa có)
            if not is_from_cache:
                current_cmd = self.txt_command.toPlainText().strip()
                self.cache.put(current_cmd, qimg)
            
            # 2. HIỂN THỊ LÊN CANVAS PHẢI
            pixmap = QPixmap.fromImage(qimg)
            should_reset = getattr(self.image_canvas, 'reset_view_flag', False)
            self.image_canvas.set_image(pixmap, reset_view=should_reset)
            self.image_canvas.reset_view_flag = False
                        
        except Exception as e:
            print(f"Right canvas error: {e}")

    def _display_qimage(self, qimg):
        """Hàm hỗ trợ hiển thị chung"""
        pixmap = QPixmap.fromImage(qimg)
        should_reset = getattr(self.image_canvas, 'reset_view_flag', False)
        self.image_canvas.set_image(pixmap, reset_view=should_reset)
        self.image_canvas.reset_view_flag = False

    # Batch processing
    def _start_batch_thread(self):
        if not self.file_structure or not self.output_dir:
            QMessageBox.warning(self, "Thiếu thông tin", "Chọn đủ Input/Output folder.")
            return
        
        if not self.current_command.strip():
            QMessageBox.warning(self, "Thiếu lệnh", "Vui lòng nhập lệnh xử lý.")
            return
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.txt_log.clear()
        
        # Pass file_structure with relative paths (strings), input_dir, and output_dir
        self.worker = BatchWorker(
            self.file_structure,
            self.input_dir,
            self.output_dir,
            self.current_command
        )
        self.worker.progress_signal.connect(self._update_batch_progress)
        self.worker.finished_signal.connect(self._batch_finished)
        self.worker.error_signal.connect(lambda e: print(e))
        self.worker.log_signal.connect(self._append_log)
        self.worker.start()
    
    def _update_batch_progress(self, current, total, filename):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _append_log(self, message):
        self.txt_log.append(message)
        self.txt_log.verticalScrollBar().setValue(
            self.txt_log.verticalScrollBar().maximum()
        )

    def _stop_batch_thread(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setText("Stopping...")

    def _batch_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setText("STOP")
        QMessageBox.information(self, "Xong", "Đã hoàn tất xử lý!")

    # Preset handlers
    def _update_presets_list(self):
        self.list_presets.clear()
        if CONFIG.preset_file.exists():
            try:
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k in sorted(data.keys()):
                        self.list_presets.addItem(k)
            except:
                pass

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Tên Preset:")
        if ok and name:
            data = {}
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except:
                        pass
            data[name] = self.current_command
            with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._update_presets_list()
            QMessageBox.information(self, "Thành công", f"Đã lưu preset '{name}'")

    def _delete_preset(self):
        item = self.list_presets.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, 'Xóa', 
            f"Xóa preset '{item.text()}'?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if item.text() in data:
                    del data[item.text()]
                    with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self._update_presets_list()

    def _load_preset_from_item(self, item):
        preset_name = item.text()
        if CONFIG.preset_file.exists():
            with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if preset_name in data:
                    self.current_command = data[preset_name]
                    self.txt_command.setPlainText(self.current_command)
                    self._execute_preview_update()

    def _show_help_dialog(self):
        dlg = HelpDialog(self)
        dlg.exec_()

    # ========== SPLIT VIEW FUNCTIONS ==========
    def _toggle_split_view(self):
        """Bật/tắt chế độ split view"""
        self.split_view_enabled = not self.split_view_enabled
        
        if self.split_view_enabled:
            self.btn_toggle_split.setText("Split View: ON")
            self.btn_toggle_split.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.image_canvas_left.show()
            
            # Reset view cho cả 2 canvas
            self.image_canvas.reset_view_flag = True
            self.image_canvas_left.reset_view_flag = True
            
            # [MỚI] Cập nhật ảnh trái ngay khi bật chế độ này
            self._update_left_canvas_once()
            
            # Trigger tạo ảnh phải
            if hasattr(self, 'cached_source_blob') and self.cached_source_blob:
                self._execute_preview_update()
        else:
            self.btn_toggle_split.setText("Split View: OFF")
            self.btn_toggle_split.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
            self.image_canvas_left.hide()
            
            self.image_canvas.reset_view_flag = True
            if hasattr(self, 'cached_source_blob') and self.cached_source_blob:
                self._execute_preview_update()
    
    def _sync_from_left(self, state):
        """Đồng bộ từ canvas TRÁI sang PHẢI"""
        # Canvas phải nhận lệnh sync
        self.image_canvas.apply_sync_state(state)
    
    def _sync_from_right(self, state):
        """Đồng bộ từ canvas PHẢI sang TRÁI"""
        if not self.split_view_enabled:
            return
        # Canvas trái nhận lệnh sync
        self.image_canvas_left.apply_sync_state(state)


