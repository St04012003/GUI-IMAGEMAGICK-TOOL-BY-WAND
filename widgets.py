# widgets.py

import re
from typing import Callable, Tuple
from qtpy.QtWidgets import QPushButton, QGroupBox, QVBoxLayout, QPlainTextEdit, QCompleter, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QKeyEvent, QTextCursor, QPainter

from config import CONFIG


# ==================
# CUSTOM UI WIDGETS
# ==================
def create_button(text: str, callback: Callable, style: str = "", height: int = None) -> QPushButton:
    """Helper to create styled button"""
    btn = QPushButton(text)
    btn.clicked.connect(callback)
    if style:
        btn.setStyleSheet(style)
    if height:
        btn.setFixedHeight(height)
    return btn

def create_groupbox(title: str, layout_type=QVBoxLayout) -> Tuple[QGroupBox, QVBoxLayout]:
    """Helper to create groupbox with layout"""
    group = QGroupBox(title)
    layout = layout_type()
    group.setLayout(layout)
    return group, layout

class CommandSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ FIX: Chuẩn hóa valid_commands - loại bỏ '-' và lowercase
        self.valid_commands = {cmd.lstrip('-').lower() for cmd in CONFIG.commands}
        
        # Style definitions
        self.styles = {
            'VALID': self._fmt("#4CAF50", bold=True),      # Green: Valid command
            'ERROR': self._fmt("#F44336", wave=True),      # Red wave: Invalid
            'NUM':   self._fmt("#9C27B0")                  # Purple: Numbers/Geometry
        }

        # Regex pattern (unchanged)
        self.pattern = re.compile(r"""
            (?P<CMD>-(?![0-9])[\w-]+) |  # Command group
            (?P<NUM>[+\-]?\d+(?:x\d+)?(?:[+\-]\d+)*\.?\d*%?) # Number group
        """, re.VERBOSE | re.IGNORECASE)

    def _fmt(self, color, bold=False, wave=False):
        """Helper to create format"""
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold: 
            f.setFontWeight(QFont.Bold)
        if wave:
            f.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            f.setUnderlineColor(QColor(color))
        return f

    def highlightBlock(self, text):
        """Highlight syntax with case-insensitive validation"""
        for match in self.pattern.finditer(text):
            if match.group('CMD'):
                # ✅ FIX: Strip '-' and lowercase for comparison
                cmd_name = match.group('CMD').lstrip('-').lower()
                
                # Choose style: VALID or ERROR
                key = 'VALID' if cmd_name in self.valid_commands else 'ERROR'
                self.setFormat(match.start(), len(match.group()), self.styles[key])
                
            elif match.group('NUM'):
                self.setFormat(match.start(), len(match.group()), self.styles['NUM'])


class SmartCommandEdit(QPlainTextEdit):
    """Text edit with case-insensitive autocomplete"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Nhập lệnh... (Gõ '-' để autocomplete)")
        
        # ✅ Autocomplete đã case-insensitive (Qt.CaseInsensitive)
        self.completer = QCompleter(CONFIG.commands, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # ✅ CRITICAL
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.activated.connect(self._insert_completion)
        
        # ✅ Use fixed highlighter
        self.highlighter = CommandSyntaxHighlighter(self.document())
    
    def _insert_completion(self, completion):
        """Insert selected command with trailing space and close popup"""
        cursor = self.textCursor()
        text = cursor.block().text()
        pos = cursor.positionInBlock()
        
        # Find start of word (tìm vị trí bắt đầu của từ đang gõ)
        start_pos = next(
            (i for i in range(pos, -1, -1) if i == 0 or text[i-1] in (' ', '\n', '\t')), 
            0
        )
        
        # Replace word with completion + space
        cursor.setPosition(cursor.block().position() + start_pos)
        cursor.setPosition(cursor.block().position() + pos, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        
        # ✅ CẢI TIẾN: Thêm khoảng trắng sau lệnh
        cursor.insertText(completion + " ")
        
        self.setTextCursor(cursor)
        
        # ✅ CẢI TIẾN: Đóng popup sau khi chèn
        self.completer.popup().hide()
    
    def _get_word_under_cursor(self):
        """Get the word under cursor position"""
        cursor = self.textCursor()
        text = cursor.block().text()
        pos = cursor.positionInBlock()
        start = next(
            (i for i in range(pos, -1, -1) if i == 0 or text[i-1] in (' ', '\n', '\t')), 
            0
        )
        return text[start:pos]
    
    def keyPressEvent(self, event: QKeyEvent):
        # ✅ CẢI TIẾN: Xử lý khi popup đang mở
        if self.completer.popup().isVisible():
            # Các phím đặc biệt khi popup đang hiển thị
            if event.key() in (Qt.Key.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab):
                if event.key() == Qt.Key_Escape:
                    # ESC: Đóng popup không chèn gì
                    self.completer.popup().hide()
                    event.accept()
                    return
                    
                elif event.key() in (Qt.Key.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                    # ENTER/TAB: Chèn lệnh được chọn + khoảng trắng + đóng popup
                    if self.completer.popup().currentIndex().isValid():
                        selected_text = self.completer.popup().currentIndex().data()
                        self._insert_completion(selected_text)
                    else:
                        # Nếu không có mục nào được chọn, chọn mục đầu tiên
                        if self.completer.completionCount() > 0:
                            self.completer.setCurrentRow(0)
                            selected_text = self.completer.currentCompletion()
                            self._insert_completion(selected_text)
                    
                    event.accept()
                    return
                    
            elif event.key() in (Qt.Key_Up, Qt.Key_Down):
                # Mũi tên lên/xuống: Di chuyển trong popup
                event.ignore()
                return
        
        # ✅ Xử lý phím bình thường
        super().keyPressEvent(event)
        
        # ✅ Hiển thị autocomplete khi gõ '-'
        word = self._get_word_under_cursor()
        
        if word.startswith('-') and len(word) > 1:  # Ít nhất '-x' mới hiện
            self.completer.setCompletionPrefix(word)
            
            if self.completer.completionCount() > 0:
                # Tính toán vị trí hiển thị popup
                cr = self.cursorRect()
                cr.setWidth(
                    self.completer.popup().sizeHintForColumn(0) + 
                    self.completer.popup().verticalScrollBar().sizeHint().width() + 10
                )
                self.completer.complete(cr)
                
                # ✅ CẢI TIẾN: Tự động chọn item đầu tiên
                if not self.completer.popup().currentIndex().isValid():
                    self.completer.popup().setCurrentIndex(
                        self.completer.completionModel().index(0, 0)
                    )
            else:
                self.completer.popup().hide()
        else:
            # Ẩn popup khi không còn gõ lệnh
            self.completer.popup().hide()

class ImageCanvas(QGraphicsView):
    """
    Canvas cải tiến với thuật toán Sync dựa trên Viewport Center & Absolute Scale.
    Đã FIX lỗi RecursionError (lặp vô tận).
    """
    def __init__(self, parent=None, sync_callback=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.sync_callback = sync_callback
        self.is_syncing = False # Cờ chặn loop vô tận
        self.reset_view_flag = False

        self.min_scale = 0.01   # Zoom out tối đa 1%
        self.max_scale = 50.0   # Zoom in tối đa 5000%
        self.zoom_factor = 1.15 # Tốc độ zoom (mượt hơn 1.2)

        # Cấu hình View
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor(30, 30, 30))
        self.setFrameShape(QFrame.NoFrame)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)

    def set_image(self, q_pixmap, reset_view=False):
        # [FIX] Khóa Sync khi đang load ảnh để tránh trigger sự kiện cuộn giả
        self.is_syncing = True
        try:
            self.pixmap_item.setPixmap(q_pixmap)
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            
            if reset_view:
                self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        finally:
            # Luôn mở khóa dù có lỗi hay không
            self.is_syncing = False

        # Sau khi load xong, nếu cần reset view thì mới gửi thông báo 1 lần duy nhất
        if reset_view:
            self._broadcast_view_state()

    def wheelEvent(self, event):
        if self.is_syncing:
            return

        # 1. Tính toán Zoom
        zoom_factor = 1.15
        scale_tr = zoom_factor if event.angleDelta().y() > 0 else 1 / zoom_factor
        
        # 2. Kiễm tra giới hạn zoom
        current_scale = self.transform().m11()
        new_scale = current_scale * scale_tr
        # Giới hạn zoom range
        if (current_scale > 20 and scale_tr > 1) or (current_scale < 0.05 and scale_tr < 1):
            return

        # 3. Lưu vị trí chuột trước khi zoom
        old_pos = self.mapToScene(event.pos())

        # 4. Thực hiện Zoom
        self.scale(scale_tr, scale_tr)

        # 5. Điều chỉnh lại vị trí zoom đúng vào điểm chuột
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

        # 6. Gửi lệnh đồng bộ
        self._broadcast_view_state()

    def scrollContentsBy(self, dx, dy):
        """Bắt sự kiện khi Pan (kéo chuột) hoặc khi View tự cuộn"""
        super().scrollContentsBy(dx, dy)
        
        # Chỉ gửi sync nếu người dùng đang thao tác (không phải do code sync gọi)
        if not self.is_syncing:
            self._broadcast_view_state()

    def _broadcast_view_state(self):
        """Gửi trạng thái hiện tại (Scale + Center Point) cho View kia"""
        if self.sync_callback and self.pixmap_item.pixmap():
            current_scale = self.transform().m11()
            center_point = self.mapToScene(self.viewport().rect().center())
            
            state = {
                'scale': current_scale,
                'center_x': center_point.x(),
                'center_y': center_point.y()
            }
            self.sync_callback(state)

    def apply_sync_state(self, state):
        """Nhận lệnh từ View kia và áp dụng"""
        if not self.pixmap_item.pixmap():
            return

        # Khóa Sync ngay lập tức trước khi thay đổi view
        self.is_syncing = True
        
        try:
            # 1. Kiểm tra giới hạn trước khi áp dụng
            target_scale = state['scale']
            if target_scale < self.min_scale or target_scale > self.max_scale:
                return
            
            # 2. Áp dụng Scale
            target_scale = state['scale']
            new_transform = self.transform()
            new_transform.reset() 
            new_transform.scale(target_scale, target_scale)
            self.setTransform(new_transform)

            # 3. Áp dụng Center (Hàm này sẽ trigger scrollContentsBy -> Cần is_syncing chặn lại)
            self.centerOn(state['center_x'], state['center_y'])
        
        except Exception as e:
            print(f"Sync error: {e}")
        
        finally:
            # Mở khóa an toàn
            self.is_syncing = False
    
    def zoom_to_fit(self):
        """Reset zoom về fit toàn bộ ảnh trong viewport"""
        if self.pixmap_item.pixmap():
            self.is_syncing = True
            try:
                self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
                self._broadcast_view_state()
            finally:
                self.is_syncing = False

    def zoom_to_100(self):
        """Reset zoom về 100% (1:1 pixel)"""
        if self.pixmap_item.pixmap():
            self.is_syncing = True
            try:
                self.resetTransform()
                self._broadcast_view_state()
            finally:
                self.is_syncing = False

    def get_current_zoom_percent(self) -> int:
        """Lấy % zoom hiện tại (dùng để hiển thị trên UI)"""
        return int(self.transform().m11() * 100)