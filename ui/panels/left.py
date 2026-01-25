import json
from pathlib import Path
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QLabel, QListWidget, 
                             QGridLayout, QMenu, QAction, QInputDialog, QMessageBox, QFileDialog)
from qtpy.QtCore import Qt, Signal

from config import CONFIG
from widgets import create_button, create_groupbox

# =============
# LEFT PANEL
# =============
class LeftPanel(QWidget):
    # Signals
    req_select_input = Signal()
    req_select_output = Signal()
    file_selected = Signal(int)
    preset_applied = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.get_current_command_callback = lambda: "" # Placeholder
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._create_io_group())
        splitter.addWidget(self._create_file_list_group())
        splitter.addWidget(self._create_presets_group())
        splitter.setSizes([120, 300, 300])
        layout.addWidget(splitter)

    def _create_io_group(self):
        group, layout = create_groupbox("I/O Settings")
        self.btn_input = create_button("Input Files/Folder", self.req_select_input.emit)
        self.lbl_input = QLabel("...")
        self.lbl_input.setWordWrap(True)
        self.btn_output = create_button("Output Folder", self.req_select_output.emit)
        self.lbl_output = QLabel("...")
        for w in [self.btn_input, self.lbl_input, self.btn_output, self.lbl_output]:
            layout.addWidget(w)
        return group

    def _create_file_list_group(self):
        group, layout = create_groupbox("Danh sách File")
        self.list_files = QListWidget()
        self.list_files.currentRowChanged.connect(self.file_selected.emit)
        layout.addWidget(self.list_files)
        return group

    def _create_presets_group(self):
        group, layout = create_groupbox("Presets Manager")
        self.list_presets = QListWidget()
        self.list_presets.itemDoubleClicked.connect(self._on_preset_dbl_click)
        self.list_presets.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_presets.customContextMenuRequested.connect(self._show_preset_context_menu)
        layout.addWidget(self.list_presets)
        
        btn_grid = QGridLayout()
        buttons = [
            (create_button("Save", self._save_preset_dialog, height=30), 0, 0),
            (create_button("Delete", self._delete_preset, height=30), 0, 1),
            (create_button("Import", self._import_presets, height=30), 1, 0),
            (create_button("Export", self._export_presets, height=30), 1, 1),
        ]
        for btn, row, col in buttons:
            btn_grid.addWidget(btn, row, col)
        layout.addLayout(btn_grid)
        self.update_presets_list()
        return group

    # --- Preset Logic ---
    def update_presets_list(self):
        self.list_presets.clear()
        if CONFIG.preset_file.exists():
            try:
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k in sorted(data.keys()):
                        self.list_presets.addItem(k)
            except: pass

    def _on_preset_dbl_click(self, item):
        preset_name = item.text()
        if CONFIG.preset_file.exists():
            with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if preset_name in data:
                    self.preset_applied.emit(data[preset_name])

    def _save_preset_dialog(self):
        cmd = self.get_current_command_callback()
        if not cmd:
            QMessageBox.warning(self, "Lỗi", "Không có lệnh nào để lưu!")
            return
        name, ok = QInputDialog.getText(self, "Save Preset", "Tên Preset:")
        if ok and name:
            data = {}
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                    try: data = json.load(f)
                    except: pass
            data[name] = cmd
            with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.update_presets_list()

    def _delete_preset(self):
        item = self.list_presets.currentItem()
        if not item: return
        reply = QMessageBox.question(self, 'Xóa', f"Xóa preset '{item.text()}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            with open(CONFIG.preset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if item.text() in data:
                del data[item.text()]
                with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.update_presets_list()

    def _import_presets(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Presets", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: new_data = json.load(f)
            current_data = {}
            if CONFIG.preset_file.exists():
                with open(CONFIG.preset_file, 'r', encoding='utf-8') as f: current_data = json.load(f)
            current_data.update(new_data)
            with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            self.update_presets_list()
            QMessageBox.information(self, "OK", "Import thành công!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))

    def _export_presets(self):
        if not CONFIG.preset_file.exists(): return
        path, _ = QFileDialog.getSaveFileName(self, "Export", "presets_backup.json", "JSON (*.json)")
        if path:
            with open(CONFIG.preset_file, 'r', encoding='utf-8') as f: content = f.read()
            with open(path, 'w', encoding='utf-8') as f: f.write(content)

    def _show_preset_context_menu(self, pos):
        item = self.list_presets.itemAt(pos)
        if not item: return
        menu = QMenu()
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_preset(item))
        menu.addAction(rename_action)
        menu.exec(self.list_presets.mapToGlobal(pos))

    def _rename_preset(self, item):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename", "Tên mới:", text=old_name)
        if ok and new_name and new_name != old_name:
            with open(CONFIG.preset_file, 'r', encoding='utf-8') as f: data = json.load(f)
            if old_name in data:
                data[new_name] = data[old_name]
                del data[old_name]
                with open(CONFIG.preset_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.update_presets_list()