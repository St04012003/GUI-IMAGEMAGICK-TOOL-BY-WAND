from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QImage, QPixmap
from wand.image import Image as WandImage

# Import Modules
from config import CONFIG
from core import ImageCache
from workers import BatchWorker, FileLoaderWorker, PreviewController
from dialog import HelpDialog

# Import UI Panels
from ui.panels.left import LeftPanel
from ui.panels.middle import MiddlePanel
from ui.panels.right import RightPanel

# =============
# MAIN WINDOW
# =============
class ImageMagickTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ImageMagick GUI Tool {CONFIG.app_version}")
        self.resize(1700, 1000)
        
        self.settings = QSettings(str(CONFIG.settings_file), QSettings.IniFormat)
        self.cache = ImageCache(max_size=30)

        # State
        self.input_dir = Path(self.settings.value("last_input_dir", ""))
        self.output_dir = Path(self.settings.value("last_output_dir", ""))
        self.image_files: List[str] = []
        self.file_structure: Dict[str, List[str]] = {}
        self.current_index = -1
        self.worker: Optional[BatchWorker] = None
        self.file_loader_worker: Optional[FileLoaderWorker] = None
        self.cached_source_blob = None
        self._preview_lock = False

        # Controllers
        self.preview_controller = PreviewController()
        self.preview_controller.preview_ready_signal.connect(self._on_preview_ready_thread_safe)
        
        # Timers
        self.ui_load_timer = QTimer()
        self.ui_load_timer.setInterval(20)
        self.ui_load_timer.timeout.connect(self._process_ui_load_queue)
        self.pending_files_queue = []

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(CONFIG.debounce_delay)
        self.debounce_timer.timeout.connect(self._execute_preview_update)

        self._init_ui()
        self._restore_settings()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)

        # Khởi tạo 3 Panel từ thư mục 'panels'
        self.left = LeftPanel()
        self.middle = MiddlePanel()
        self.right = RightPanel()

        # Wiring: Kết nối Left Panel để lấy text khi Save Preset
        self.left.get_current_command_callback = lambda: self.right.txt_command.toPlainText().strip()

        # Layout
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.left)
        main_splitter.addWidget(self.middle)
        main_splitter.addWidget(self.right)
        main_splitter.setSizes([250, 1000, 400])
        layout.addWidget(main_splitter)

        # === KẾT NỐI TÍN HIỆU (SIGNALS) ===
        # Left
        self.left.req_select_input.connect(self._select_input)
        self.left.req_select_output.connect(self._select_output)
        self.left.file_selected.connect(self._on_file_changed)
        self.left.preset_applied.connect(self._on_preset_applied)
        # Middle
        self.middle.req_prev_image.connect(self._prev_image)
        self.middle.req_next_image.connect(self._next_image)
        self.middle.req_refresh_preview.connect(self._refresh_split_view_logic)
        # Right
        self.right.command_changed.connect(self._on_command_input_changed)
        self.right.req_start_batch.connect(self._start_batch_thread)
        self.right.req_stop_batch.connect(self._stop_batch_thread)
        self.right.req_help.connect(self._show_help)

    def _restore_settings(self):
        if self.input_dir.exists():
            self.left.lbl_input.setText(str(self.input_dir))
        if self.output_dir.exists():
            self.left.lbl_output.setText(self.output_dir.name)

    # --- LOGIC XỬ LÝ (Giữ nguyên như cũ) ---
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
            files, _ = QFileDialog.getOpenFileNames(self, "Chọn file", start_dir, f"Images ({' '.join(['*' + e for e in CONFIG.image_extensions])})")
            if files:
                self.input_dir = Path(files[0]).parent
                file_names = sorted([Path(f).name for f in files])
                self.file_structure = {"": file_names}
                self.image_files = file_names
                self._finalize_load_files(len(files))
                
        elif msg.clickedButton() == btn_folder:
            d = QFileDialog.getExistingDirectory(self, "Chọn Folder", start_dir)
            if d:
                self.input_dir = Path(d)
                self.left.list_files.clear()
                self.left.list_files.addItem("Đang quét file...")
                self.left.btn_input.setEnabled(False) 
                self.file_loader_worker = FileLoaderWorker(self.input_dir, CONFIG.image_extensions)
                self.file_loader_worker.finished_signal.connect(self._on_scan_finished)
                self.file_loader_worker.start()

    def _on_scan_finished(self, structure, flat_list, total_count):
        self.file_structure = structure
        self.image_files = flat_list
        self.left.btn_input.setEnabled(True)
        if total_count == 0:
            self.left.list_files.clear()
            self.left.list_files.addItem("(Empty)")
            return
        self._finalize_load_files(total_count)

    def _select_output(self):
        start_dir = str(self.output_dir) if self.output_dir.exists() else ""
        d = QFileDialog.getExistingDirectory(self, "Output Folder", start_dir)
        if d:
            self.output_dir = Path(d)
            self.left.lbl_output.setText(self.output_dir.name)

    def _finalize_load_files(self, total_count):
        self.left.lbl_input.setText(f"{self.input_dir.name} ({total_count})")
        self.left.list_files.clear()
        self.pending_files_queue = list(self.image_files)
        initial = self.pending_files_queue[:50]
        self.left.list_files.addItems(initial)
        del self.pending_files_queue[:50]
        if self.image_files:
            self.current_index = 0
            self.left.list_files.setCurrentRow(0)
        if self.pending_files_queue:
            self.ui_load_timer.start()

    def _process_ui_load_queue(self):
        if not self.pending_files_queue:
            self.ui_load_timer.stop()
            return
        batch = self.pending_files_queue[:200]
        self.left.list_files.addItems(batch)
        del self.pending_files_queue[:200]

    def _on_file_changed(self, index):
        if 0 <= index < len(self.image_files):
            self.current_index = index
            self._load_image_to_memory()

    def _prev_image(self):
        if self.current_index > 0:
            self.left.list_files.setCurrentRow(self.current_index - 1)

    def _next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.left.list_files.setCurrentRow(self.current_index + 1)

    def _load_image_to_memory(self):
        filepath = self.input_dir / self.image_files[self.current_index]
        self.debounce_timer.stop()
        self.cache.clear()
        self.cached_source_blob = None
        try:
            with open(filepath, 'rb') as f: img_blob = f.read()
            with WandImage(blob=img_blob) as img:
                if img.width > 1200 or img.height > 1200: img.transform(resize="800x1200>")
                self.cached_source_blob = img.make_blob(format='bmp')
            self.middle.lbl_info.setText(f"{self.current_index + 1}/{len(self.image_files)}: {filepath.name}")
            self.middle.image_canvas.reset_view_flag = True
            if self.middle.split_view_enabled: self._update_left_canvas()
            self._execute_preview_update()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi đọc ảnh", str(e))

    def _on_command_input_changed(self):
        self.debounce_timer.start()

    def _on_preset_applied(self, cmd_str):
        self.right.txt_command.setPlainText(cmd_str)
        self._execute_preview_update()

    def _refresh_split_view_logic(self):
        if self.middle.split_view_enabled: self._update_left_canvas()
        self._execute_preview_update()

    def _update_left_canvas(self):
        if self.cached_source_blob:
            qimg = QImage.fromData(self.cached_source_blob)
            self.middle.image_canvas_left.set_image(QPixmap.fromImage(qimg), reset_view=self.middle.image_canvas_left.reset_view_flag)
            self.middle.image_canvas_left.reset_view_flag = False

    def _execute_preview_update(self):
        if not self.cached_source_blob or self._preview_lock: return
        cmd = self.right.txt_command.toPlainText().strip()
        cached_qimg = self.cache.get(cmd)
        if cached_qimg:
            self._update_right_display(cached_qimg)
            return
        self._preview_lock = True
        self.preview_controller.request_preview(self.cached_source_blob, cmd)

    def _on_preview_ready_thread_safe(self, blob_data):
        self._preview_lock = False
        try:
            qimg = QImage.fromData(blob_data)
            cmd = self.right.txt_command.toPlainText().strip()
            self.cache.put(cmd, qimg)
            self._update_right_display(qimg)
        except Exception as e:
            print(f"Error preview: {e}")

    def _update_right_display(self, qimg):
        pixmap = QPixmap.fromImage(qimg)
        self.middle.image_canvas.set_image(pixmap, reset_view=self.middle.image_canvas.reset_view_flag)
        self.middle.image_canvas.reset_view_flag = False

    def _start_batch_thread(self):
        cmd = self.right.txt_command.toPlainText().strip()
        if not self.file_structure or not self.output_dir:
            QMessageBox.warning(self, "Thiếu thông tin", "Chọn đủ Input/Output folder.")
            return
        if not cmd:
            QMessageBox.warning(self, "Thiếu lệnh", "Vui lòng nhập lệnh.")
            return
        self.right.btn_start.setEnabled(False)
        self.right.btn_stop.setEnabled(True)
        self.right.progress_bar.setValue(0)
        self.right.txt_log.clear()
        self.worker = BatchWorker(self.file_structure, self.input_dir, self.output_dir, cmd)
        self.worker.progress_signal.connect(lambda c, t, f: self.right.progress_bar.setValue(c) or self.right.progress_bar.setMaximum(t))
        self.worker.log_signal.connect(self.right.append_log)
        self.worker.finished_signal.connect(self._batch_finished)
        self.worker.start()

    def _stop_batch_thread(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.right.btn_stop.setText("Stopping...")

    def _batch_finished(self):
        self.right.btn_start.setEnabled(True)
        self.right.btn_stop.setEnabled(False)
        self.right.btn_stop.setText("STOP")
        QMessageBox.information(self, "Xong", "Hoàn tất xử lý!")

    def _show_help(self):
        HelpDialog(self).exec_()

    def closeEvent(self, event):
        if self.output_dir: self.settings.setValue("last_output_dir", str(self.output_dir))
        if self.input_dir and self.input_dir.exists(): self.settings.setValue("last_input_dir", str(self.input_dir))
        if self.preview_controller: self.preview_controller.shutdown()
        if self.worker and self.worker.isRunning(): 
            self.worker.stop()
            self.worker.terminate()
        event.accept()