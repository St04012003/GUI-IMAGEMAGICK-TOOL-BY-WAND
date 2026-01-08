# 6.dialogs.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QTextBrowser


# =============
# HELP DIALOG 
# =============
class HelpDialog(QDialog):
    """Dialog hướng dẫn sử dụng và tra cứu lệnh"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hướng dẫn & Tra cứu lệnh ImageMagick")
        self.resize(1100, 800)
        
        # Set style chung cho Dialog (Light Theme)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; color: #333333; }
            QTabWidget::pane { border: 1px solid #cccccc; }
            QTabBar::tab { background: #e0e0e0; color: #333; padding: 8px 20px; font-size: 13px; }
            QTabBar::tab:selected { background: #ffffff; color: #000; border-bottom: 3px solid #2196F3; font-weight: bold; }
            QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #e0e0e0; border-color: #bbb; }
            QTextBrowser { border: none; padding: 10px; }
        """)

        # Layout chính
        layout = QVBoxLayout(self)
        
        # Tạo Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_guide_tab(), "📖 Hướng dẫn nhanh")
        self.tabs.addTab(self._create_reference_tab(), "🔍 Tra cứu lệnh (Full)")
        
        layout.addWidget(self.tabs)
        
        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedWidth(100)
        
        # Căn nút đóng ra giữa/phải
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _create_guide_tab(self):
        """Tab hướng dẫn cơ bản"""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        
        browser.setHtml("""
        <style>
            body { font-family: Segoe UI, sans-serif; color: #333; line-height: 1.6; }
            h1 { color: #C2185B; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
            h2 { color: #1976D2; margin-top: 25px; margin-bottom: 10px; }
            li { margin-bottom: 8px; font-size: 14px; }
            p { margin-bottom: 10px; }
            
            /* Khung Code */
            pre { 
                background-color: #f5f5f5; 
                color: #2E7D32; 
                padding: 12px; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                font-family: Consolas, monospace;
                font-weight: bold;
                font-size: 13px;
            }
            
            /* Highlight từ khóa */
            .key { font-weight: bold; color: #E65100; background-color: #fff3e0; padding: 2px 5px; border-radius: 3px; }
            code { background-color: #eee; padding: 2px 4px; border-radius: 3px; font-family: Consolas; color: #333; }
        </style>
        
        <h1>ImageMagick GUI Tool </h1>
        
        <h2>🚀 Quy trình xử lý ảnh</h2>
        <ol>
            <li><b>Bước 1:</b> Chọn <span class="key">Input</span> (File lẻ hoặc Folder chứa truyện).</li>
            <li><b>Bước 2:</b> Chọn <span class="key">Output Folder</span> (Nơi lưu kết quả).</li>
            <li><b>Bước 3:</b> Nhập lệnh vào ô Command (Gõ dấu <code>-</code> để xem gợi ý thông minh).</li>
            <li><b>Bước 4:</b> Sử dụng chế độ <span class="key">Split View</span> để so sánh ảnh gốc và ảnh sau xử lý.</li>
            <li><b>Bước 5:</b> Bấm <span class="key">START BATCH</span> để chạy hàng loạt.</li>
        </ol>

        <h2>⚡ Các Combo lệnh thông dụng</h2>
        <p><b>1. Resize và Xoay ảnh:</b></p>
        <pre>-resize 800x1200 -auto-orient</pre>
        
        <p><b>2. Xử lý ảnh Scan (Làm trắng nền, đậm chữ):</b></p>
        <pre>-grayscale -despeckle -level 10%,90% -sharpen 0x1</pre>
        
        <p><b>3. Giảm dung lượng giữ nguyên chất lượng:</b></p>
        <pre>-strip -quality 85 -depth 8</pre>
        
        <p><b>4. Hiệu ứng nghệ thuật (Phim cũ):</b></p>
        <pre>-sepia-tone 80% -vignette 0x20</pre>
        
        <h2>💡 Mẹo sử dụng</h2>
        <ul>
            <li><b>Split View:</b> Bật chế độ này để so sánh trực quan Before/After. Bạn có thể zoom/pan đồng bộ cả 2 bên.</li>
            <li><b>Presets:</b> Chuột phải vào preset để đổi tên. Dùng nút Import/Export để chia sẻ công thức.</li>
            <li><b>Natural Sort:</b> Tool tự động sắp xếp file thông minh (Chapter 1 -> Chapter 2... -> Chapter 10).</li>
        </ul>
        """)
        return browser

    def _create_reference_tab(self):
        """Tab tra cứu tất cả các lệnh (Cập nhật đầy đủ theo CommandParser mới)"""
        browser = QTextBrowser()
        
        # Định nghĩa danh mục lệnh
        categories = {
            "⚙️ Cài đặt ảnh & Metadata (Settings)": {
                "-quality": "Chất lượng nén JPEG/PNG (0-100, VD: 90)",
                "-density": "Đặt độ phân giải DPI (VD: 300 hoặc 300x300)",
                "-units": "Đơn vị đo (PixelsPerInch / PixelsPerCentimeter)",
                "-depth": "Độ sâu bit màu (8, 16, 32)",
                "-strip": "Xóa toàn bộ EXIF/Metadata để giảm dung lượng file",
                "-compress": "Kiểu nén (JPEG, LZW, ZIP, None...)",
                "-virtual-pixel": "Cách xử lý biên ảnh (transparent, white, black, mirror...)",
            },
            "📐 Hình học & Transform (Geometry)": {
                "-resize": "Thay đổi kích thước giữ tỷ lệ (VD: 800x600, 50%)",
                "-scale": "Resize nhanh (pixel mixing, không nội suy)",
                "-sample": "Resize giữ nguyên pixel (nearest neighbor - Pixel Art)",
                "-liquid-rescale": "Seam carving (Co giãn bảo toàn nội dung)",
                "-crop": "Cắt ảnh (VD: 800x600+10+10)",
                "-extent": "Thay đổi kích thước canvas (Thêm viền/Cắt bớt)",
                "-repage": "Đặt lại canvas ảo (Dùng sau khi crop/trim)",
                "-trim": "Tự động cắt bỏ viền thừa đồng màu",
                "-rotate": "Xoay ảnh (độ)",
                "-auto-orient": "Tự động xoay ảnh đúng chiều (dựa theo EXIF)",
                "-deskew": "Tự động làm thẳng ảnh scan bị nghiêng",
                "-flip / -flop": "Lật dọc / Lật ngang",
            },
            "🎨 Màu sắc & Levels (Color)": {
                "-grayscale": "Chuyển sang đen trắng (Grayscale)",
                "-monochrome": "Chuyển sang đen trắng 2 màu (Dithered 1-bit)",
                "-level": "Chỉnh Levels (Black,White,Gamma - VD: 10%,90%)",
                "-auto-level": "Tự động cân bằng mức màu",
                "-brightness-contrast": "Chỉnh Độ sáng/Tương phản (VD: 10x20)",
                "-gamma": "Điều chỉnh Gamma correction",
                "-threshold": "Ngưỡng đen trắng (VD: 50%)",
                "-black-threshold": "Biến các pixel dưới ngưỡng thành đen",
                "-white-threshold": "Biến các pixel trên ngưỡng thành trắng",
                "-negate": "Đảo ngược màu (Âm bản)",
                "-colorspace": "Đổi hệ màu (gray, rgb, cmyk, hsl...)",
                "-transparent": "Biến một màu thành trong suốt (VD: white)",
                "-background": "Đặt màu nền mặc định",
            },
            "💧 Bộ lọc & Khử nhiễu (Filters)": {
                "-blur": "Làm mờ cơ bản (Radius x Sigma)",
                "-gaussian-blur": "Làm mờ Gaussian (Mịn hơn)",
                "-sharpen": "Làm nét ảnh (Radius x Sigma)",
                "-unsharp": "Làm nét Unsharp Mask (Chuyên dụng)",
                "-despeckle": "Khử nhiễu đốm (Tốt cho ảnh scan)",
                "-reduce-noise": "Khử nhiễu tổng quát",
                "-median": "Lọc trung vị (Khử nhiễu muối tiêu)",
                "-enhance": "Tăng cường chất lượng (Khử nhiễu số)",
                "-kuwahara": "Làm mịn bảo toàn cạnh (Hiệu ứng tranh vẽ)",
            },
            "🌀 Nghệ thuật (Artistic)": {
                "-sepia-tone": "Hiệu ứng màu phim cũ",
                "-solarize": "Hiệu ứng phơi sáng quá mức",
                "-posterize": "Giảm số lượng cấp độ màu",
                "-oil-paint": "Tranh sơn dầu",
                "-charcoal": "Vẽ than chì",
                "-sketch": "Vẽ phác thảo",
                "-vignette": "Làm tối 4 góc ảnh",
                "-polaroid": "Khung ảnh Polaroid + Bóng đổ",
                "-blue-shift": "Giả lập hiệu ứng ban đêm",
            },
             "🖼️ Trang trí (Decoration)": {
                "-border": "Thêm viền (Width x Height)",
                "-frame": "Thêm khung tranh 3D",
                "-edge": "Tách biên/cạnh của ảnh",
                "-canny": "Dò cạnh Canny (Nâng cao)",
            }
        }

        # Tạo HTML Table
        html = """
        <style>
            body { font-family: Segoe UI, sans-serif; }
            
            /* Header Nhóm */
            h3 { 
                background-color: #e3f2fd; 
                color: #0d47a1; 
                padding: 10px; 
                border-radius: 4px; 
                border-left: 5px solid #1976D2;
                margin-top: 25px;
                margin-bottom: 10px;
                font-size: 15px;
            }
            
            table { width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px; }
            
            th { text-align: left; background-color: #1976D2; color: white; padding: 10px; border: 1px solid #1976D2; }
            td { border: 1px solid #ddd; padding: 8px 10px; color: #333; vertical-align: top; }
            
            /* Zebra striping */
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:nth-child(odd) { background-color: #ffffff; }
            
            /* Cột lệnh */
            .cmd { 
                color: #d32f2f; 
                font-weight: bold; 
                font-family: Consolas, monospace; 
                white-space: nowrap;
            }
        </style>
        """
        
        for category, commands in categories.items():
            html += f"<h3>{category}</h3>"
            html += "<table><tr><th width='30%'>Lệnh</th><th>Mô tả</th></tr>"
            for cmd, desc in commands.items():
                html += f"<tr><td class='cmd'>{cmd}</td><td>{desc}</td></tr>"
            html += "</table>"
            
        browser.setHtml(html)

        return browser
