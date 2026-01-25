# core/cmd_color.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# ==========================================
# 3. COLOR & CHANNEL (Màu sắc & Kênh màu)
# ==========================================
class ColorCommands(BaseCommand):
    @staticmethod
    def _cmd_colorspace(img, v):
        """
        Chuyển đổi không gian màu (Colorspace).
        Giá trị: gray, rgb, cmyk, srgb, hsl, hsb, lab...
        """
        if not v:
            raise ValidationError("colorspace: thiếu giá trị")
        
        valid = ['rgb', 'srgb', 'gray', 'cmyk', 'hsl', 'hsb', 'lab', 'xyz']
        cs = Validator.validate_enum(v, valid, "colorspace")
        try:
            img.transform_colorspace(cs)
        except Exception as e:
            raise ValidationError(f"colorspace: không thể chuyển đổi - {e}")

    @staticmethod
    def _cmd_type(img, v):
        """
        Thiết lập kiểu lưu trữ ảnh (Image Type).
        Giá trị: grayscale, bilevel, truecolor, palette, optimize...
        """
        if not v:
            raise ValidationError("type: thiếu giá trị")
        
        valid = ['bilevel', 'grayscale', 'palette', 'truecolor', 'colorseparation', 'optimize']
        img_type = Validator.validate_enum(v, valid, "type")
        img.type = img_type
        
    @staticmethod
    def _cmd_monochrome(img, v):
        """
        Chuyển thành ảnh đen trắng 2 màu (1-bit dithered).
        Tốt cho việc chuẩn bị ảnh để in laser hoặc bitmap.
        """
        img.type = 'bilevel'

    @staticmethod
    def _cmd_grayscale(img, v):
        """
        Chuyển thành ảnh xám (Grayscale - 8/16 bit).
        Giữ lại chi tiết ánh sáng, loại bỏ màu sắc.
        """
        img.type = 'grayscale'

    @staticmethod
    def _cmd_alpha(img, v):
        """
        Bật/Tắt kênh trong suốt (Alpha Channel).
        Giá trị: on, off, activate, deactivate, set, opaque...
        """
        if not v:
            raise ValidationError("alpha: thiếu tham số")
        
        valid = ['activate', 'deactivate', 'set', 'opaque', 'transparent', 'extract', 'copy', 'shape', 'on', 'off']
        mode = Validator.validate_enum(v, valid, "alpha")
        
        if mode == 'on': mode = 'activate'
        if mode == 'off': mode = 'deactivate'
        
        img.alpha_channel = mode

    @staticmethod
    def _cmd_background(img, v):
        """
        Đặt màu nền mặc định (Background Color).
        Dùng cho các lệnh rotate, extent, shear... VD: white, #FF0000.
        """
        if not v:
            raise ValidationError("background: thiếu mã màu")
        img.background_color = Validator.validate_color(v)

    @staticmethod
    def _cmd_transparent(img, v):
        """
        Biến một màu cụ thể thành trong suốt.
        VD: white (biến nền trắng thành trong suốt).
        """
        if not v:
            raise ValidationError("transparent: thiếu mã màu")
        color = Validator.validate_color(v)
        img.transparent_color(color, alpha=0.0)

    @staticmethod
    def _cmd_negate(img, v):
        """
        Đảo ngược màu sắc (Invert/Negative).
        Biến ảnh thành phim âm bản.
        """
        img.negate()

    @staticmethod
    def _cmd_level(img, v):
        """
        Điều chỉnh mức độ Black/White point và Gamma.
        Cú pháp: Black,White,Gamma. (VD: 10%,90%,1.0).
        """
        if not v:
            raise ValidationError("level: thiếu tham số")
        
        parts = v.split(',')
        black = Validator.validate_float(parts[0], "black point", 0, 100) / 100.0
        white = Validator.validate_float(parts[1], "white point", 0, 100) / 100.0 if len(parts) > 1 else 1.0
        gamma = Validator.validate_float(parts[2], "gamma", 0.1, 10) if len(parts) > 2 else 1.0
        
        img.level(black, white, gamma)

    @staticmethod
    def _cmd_auto_level(img, v):
        """Tự động kéo giãn histogram để cân bằng màu sắc (Auto Level)."""
        img.auto_level()

    @staticmethod
    def _cmd_auto_gamma(img, v):
        """Tự động điều chỉnh Gamma (Auto Gamma)."""
        img.auto_gamma()

    @staticmethod
    def _cmd_brightness_contrast(img, v):
        """
        Chỉnh độ sáng và tương phản.
        Cú pháp: Brightness x Contrast. (VD: 10x20, -10x5).
        """
        if not v:
            raise ValidationError("brightness-contrast: thiếu tham số")
            
        parts = re.split(r'[x,]', v)
        b = Validator.validate_float(parts[0], "brightness", -100, 100)
        c = Validator.validate_float(parts[1], "contrast", -100, 100) if len(parts) > 1 else 0
        
        img.brightness_contrast(b, c)

    @staticmethod
    def _cmd_modulate(img, v):
        """
        Chỉnh HSL (Độ sáng, Bão hòa, Tông màu).
        Cú pháp: Brightness,Saturation,Hue. Chuẩn là 100. (VD: 100,0,100 -> Đen trắng).
        """
        if not v:
            raise ValidationError("modulate: thiếu tham số (brightness,saturation,hue)")
        
        parts = v.split(',')
        b = Validator.validate_float(parts[0], "brightness", 0, 200)
        s = Validator.validate_float(parts[1], "saturation", 0, 200) if len(parts) > 1 else 100
        h = Validator.validate_float(parts[2], "hue", 0, 200) if len(parts) > 2 else 100
        
        img.modulate(brightness=b, saturation=s, hue=h)

    @staticmethod
    def _cmd_normalize(img, v):
        """Chuẩn hóa Histogram (Tăng tương phản tự động)."""
        img.normalize()

    @staticmethod
    def _cmd_equalize(img, v):
        """Cân bằng Histogram (Tăng chi tiết vùng tối/sáng)."""
        img.equalize()

    @staticmethod
    def _cmd_gamma(img, v):
        """
        Điều chỉnh Gamma correction.
        VD: 1.6 (Làm ảnh sáng hơn), 0.8 (Làm ảnh tối hơn).
        """
        if not v:
            raise ValidationError("gamma: thiếu giá trị")
        g = Validator.validate_float(v, "gamma", 0.1, 10.0)
        img.gamma(g)

    @staticmethod
    def _cmd_threshold(img, v):
        """
        Phân ngưỡng đen/trắng (Binary Threshold).
        Giá trị: Mức ngưỡng (VD: 50%, 128). Biến ảnh thành nhị phân.
        """
        if not v:
            raise ValidationError("threshold: thiếu giá trị")
        
        t = 0.5
        if '%' in v:
            t = Validator.validate_percentage(v, "threshold")
        else:
            t = float(v) / 255.0
            
        img.threshold(t)

    @staticmethod
    def _cmd_colorize(img, v):
        """
        Tô màu phủ lên ảnh (Colorize).
        Cú pháp: Color,Alpha. (VD: red,50 hoặc #00FF00,30).
        """
        if not v:
            raise ValidationError("colorize: thiếu màu")
        
        parts = v.split(',')
        color = Validator.validate_color(parts[0])
        alpha = parts[1] if len(parts) > 1 else "100%"
        
        img.colorize(color=color, alpha=alpha)
    
    @staticmethod
    def _cmd_tint(img, v):
        """
        Nhuộm màu ảnh (Tint).
        Cú pháp: Color,Alpha. (VD: red,50 hoặc #00FF00,30).
        """
        if not v:
            raise ValidationError("tint: thiếu màu")
        
        parts = v.split(',')
        color = Validator.validate_color(parts[0])
        alpha = parts[1] if len(parts) > 1 else "100%"
        
        img.tint(color=color, alpha=alpha)

    @staticmethod
    def _cmd_sigmoidal_contrast(img, v):
        """
        Tăng tương phản phi tuyến tính (Sigmoidal - S-Curve).
        Cú pháp: Contrast x Midpoint. (VD: 3x50%).
        Contrast: 3-20 (Độ gắt). Midpoint: 50% (Điểm giữa).
        """
        if not v:
            raise ValidationError("sigmoidal-contrast: thiếu tham số (VD: 3x50%)")
        
        parts = re.split(r'[x,]', v)
        contrast = Validator.validate_float(parts[0], "contrast", 0.1, 50)
        
        # Xử lý Midpoint (có thể là % hoặc 0-1)
        mid_str = parts[1] if len(parts) > 1 else "50%"
        if '%' in mid_str:
            midpoint = Validator.validate_percentage(mid_str, "midpoint")
        else:
            midpoint = float(mid_str)
            
        img.sigmoidal_contrast(contrast=contrast, midpoint=midpoint)

    @staticmethod
    def _cmd_auto_threshold(img, v):
        """
        Tự động phân ngưỡng đen trắng (Auto Threshold).
        Phương pháp: otsu, triangle, kapur (Mặc định: otsu).
        """
        method = 'otsu'
        if v:
            valid_methods = ['otsu', 'triangle', 'kapur']
            method = Validator.validate_enum(v, valid_methods, "auto-threshold method")
        
        img.auto_threshold(method=method)

    @staticmethod
    def _cmd_clahe(img, v):
        """
        Cân bằng Histogram cục bộ (CLAHE - Contrast Limited Adaptive Histogram Equalization).
        Cú pháp: Width x Height x Bins x ClipLimit. (VD: 50x50x128x3).
        Tăng chi tiết ảnh phong cảnh/ngược sáng rất tốt.
        """
        if not v:
            raise ValidationError("clahe: thiếu tham số (VD: 50x50x128x3)")
            
        parts = re.split(r'[x,]', v)
        # Kích thước vùng cục bộ (Tiles)
        w = Validator.validate_positive_int(parts[0], "tile width")
        h = Validator.validate_positive_int(parts[1], "tile height") if len(parts) > 1 else w
        # Số lượng bin histogram
        bins = Validator.validate_positive_int(parts[2], "number bins") if len(parts) > 2 else 128
        # Giới hạn tương phản (tránh nhiễu)
        clip = Validator.validate_float(parts[3], "clip limit", 0.1, 100) if len(parts) > 3 else 3.0
        
        img.clahe(width=w, height=h, number_bins=bins, clip_limit=clip)

    @staticmethod
    def _cmd_black_threshold(img, v):
        """
        Gán tất cả pixel tối hơn ngưỡng thành màu đen (Black Threshold).
        Tham số: Ngưỡng (VD: 50%, 128).
        """
        if not v:
            raise ValidationError("black-threshold: thiếu giá trị")
        
        threshold = v
        # Wand hỗ trợ string trực tiếp cho threshold (VD: "50%")
        img.black_threshold(threshold=threshold)

    @staticmethod
    def _cmd_white_threshold(img, v):
        """
        Gán tất cả pixel sáng hơn ngưỡng thành màu trắng (White Threshold).
        Tham số: Ngưỡng (VD: 80%, 200).
        """
        if not v:
            raise ValidationError("white-threshold: thiếu giá trị")
            
        threshold = v
        img.white_threshold(threshold=threshold)