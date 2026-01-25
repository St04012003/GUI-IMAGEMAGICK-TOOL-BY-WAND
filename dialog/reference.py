# v2.0/dialog/reference.py

from qtpy.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from qtpy.QtCore import Qt

from .styles import DIALOG_STYLES, TABLE_STYLE
from core.commands import ALL_COMMANDS

# Map tên file code sang Tiêu đề hiển thị cho đẹp
# (Bạn vẫn nên giữ cái này để phân nhóm rõ ràng)
MODULE_TITLES = {
    'cmd_settings': "⚙️ Cài đặt ảnh & Metadata (Settings)",
    'cmd_geometry': "📐 Hình học & Transform (Geometry)",
    'cmd_filter': "💧 Bộ lọc & Khử nhiễu (Filters)",
    'cmd_color': "🎨 Màu sắc & Levels (Color)",
    'cmd_artistic': "🌀 Nghệ thuật (Artistic)",
    'cmd_decoration': "🖼️ Trang trí & Khung viền (Decoration)",
    'cmd_edge': "🔪 Xử lý cạnh & Chi tiết (Edge)",
}

def _build_reference_html():
    """
    Tạo HTML table với chiều rộng cột được ép cứng (Hard-coded width).
    Khắc phục lỗi bảng lệnh ngắn (Artistic) bị lệch so với bảng lệnh dài.
    """
    grouped_commands = {}
    
    # 1. Gom nhóm lệnh (Logic cũ giữ nguyên)
    for cmd_name, func in ALL_COMMANDS.items():
        module_name = func.__module__.split('.')[-1]
        if module_name not in grouped_commands:
            grouped_commands[module_name] = []
        
        # Xử lý docstring
        full_doc = func.__doc__.strip() if func.__doc__ else "Chưa có mô tả"
        lines = [line.strip() for line in full_doc.split('\n') if line.strip()]
        description = "<br>".join(lines)
            
        grouped_commands[module_name].append((f"-{cmd_name}", description))

    # 2. Xây dựng HTML
    html = TABLE_STYLE
    html += "<div class='ref-container'>"

    sorted_modules = sorted(
        grouped_commands.keys(),
        key=lambda k: list(MODULE_TITLES.keys()).index(k) if k in MODULE_TITLES else 999
    )

    for mod_name in sorted_modules:
        title = MODULE_TITLES.get(mod_name, f"📁 {mod_name.replace('_', ' ').title()}")
        commands = sorted(grouped_commands[mod_name])

        html += f"<h3>{title}</h3>"
        
        # [FIX 1] Thêm width='100%' trực tiếp vào thẻ table
        html += "<table width='100%'>"
        
        # [FIX 2] Thêm width='40%' và '60%' trực tiếp vào thẻ th
        # Điều này bắt buộc mọi bảng phải tuân theo tỷ lệ này bất kể nội dung
        html += """
            <tr>
                <th width="40%">Lệnh</th>
                <th width="60%">Mô tả chức năng</th>
            </tr>
        """
        
        for cmd, desc in commands:
            html += f"<tr><td><code>{cmd}</code></td><td>{desc}</td></tr>"
        
        html += "</table>"

    html += "</div>"
    return html

class ReferenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Tra cứu lệnh (Command Reference)")
        self.resize(850, 600) # Kích thước mặc định rộng hơn chút để dễ đọc
        self.setStyleSheet(DIALOG_STYLES)
        
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        # Load HTML
        self.browser.setHtml(_build_reference_html())
        
        layout.addWidget(self.browser)