# dialog/reference.py
from .styles import TABLE_STYLE

# Định nghĩa danh mục lệnh
COMMAND_CATEGORIES = {
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

def _build_reference_html():
    """Tạo HTML table từ categories"""
    html = TABLE_STYLE
    
    for category, commands in COMMAND_CATEGORIES.items():
        html += f"<h3>{category}</h3>"
        html += "<table><tr><th width='30%'>Lệnh</th><th>Mô tả</th></tr>"
        
        for cmd, desc in commands.items():
            html += f"<tr><td class='cmd'>{cmd}</td><td>{desc}</td></tr>"
        
        html += "</table>"
    
    return html

REFERENCE_CONTENT = _build_reference_html()