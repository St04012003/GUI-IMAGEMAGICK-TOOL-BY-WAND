from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel)
from qtpy.QtCore import Qt, Signal

from widgets import ImageCanvas, create_button

# =============
# MIDDLE PANEL
# =============
class MiddlePanel(QWidget):
    req_prev_image = Signal()
    req_next_image = Signal()
    req_refresh_preview = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.split_view_enabled = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview Area
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(2)
        
        self.image_canvas = ImageCanvas(sync_callback=self._sync_from_right)
        self.image_canvas_left = ImageCanvas(sync_callback=self._sync_from_left)
        self.image_canvas_left.hide()
        
        self.preview_layout.addWidget(self.image_canvas_left)
        self.preview_layout.addWidget(self.image_canvas)
        
        # Navigation Bar
        nav_layout = QHBoxLayout()
        self.btn_prev = create_button("◄ Prev", self.req_prev_image.emit)
        self.btn_next = create_button("Next ►", self.req_next_image.emit)
        
        self.btn_toggle_split = create_button(
            "Split View: OFF", self._toggle_split_view,
            "background-color: #607D8B; color: white; font-weight: bold;", 35
        )
        
        self.lbl_info = QLabel("No Image")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_info, 1)
        nav_layout.addWidget(self.btn_toggle_split)
        nav_layout.addWidget(self.btn_next)
        
        layout.addWidget(self.preview_container)
        layout.addLayout(nav_layout)

    def _toggle_split_view(self):
        self.split_view_enabled = not self.split_view_enabled
        if self.split_view_enabled:
            self.btn_toggle_split.setText("Split View: ON")
            self.btn_toggle_split.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.image_canvas_left.show()
            self.image_canvas.reset_view_flag = True
            self.image_canvas_left.reset_view_flag = True
        else:
            self.btn_toggle_split.setText("Split View: OFF")
            self.btn_toggle_split.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
            self.image_canvas_left.hide()
            self.image_canvas.reset_view_flag = True
        
        self.req_refresh_preview.emit()

    def _sync_from_left(self, state):
        self.image_canvas.apply_sync_state(state)
    
    def _sync_from_right(self, state):
        if self.split_view_enabled:
            self.image_canvas_left.apply_sync_state(state)