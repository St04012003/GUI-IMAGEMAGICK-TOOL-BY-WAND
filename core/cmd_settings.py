# core/cmd_settings.py
import re
from .validator import Validator, ValidationError

# 2. IMAGE SETTINGS & METADATA (Cài đặt & Dữ liệu ảnh)

class SettingsCommands:
    @staticmethod    
    def _cmd_quality(img, v):
        # Thiết lập chất lượng nén (JPEG/PNG compression level)
        if not v:
            raise ValidationError("quality: thiếu giá trị (0-100)")
        
        quality = Validator.validate_positive_int(v, "quality", allow_zero=True)
        if quality > 100:
            raise ValidationError("quality: giá trị phải từ 0-100")
        img.compression_quality = quality

    @staticmethod
    def _cmd_density(img, v):
        # Thiết lập DPI (Resolution). Cú pháp: 300 hoặc 300x300
        if not v:
            raise ValidationError("density: thiếu giá trị DPI")
        
        parts = re.split(r'[x,]', v)
        x = Validator.validate_float(parts[0], "density X", 1, 10000)
        y = x if len(parts) == 1 else Validator.validate_float(parts[1], "density Y", 1, 10000)
        img.resolution = (x, y)

    @staticmethod
    def _cmd_units(img, v):
        # Undefined, PixelsPerInch, PixelsPerCentimeter
        if not v:
            raise ValidationError("units: thiếu giá trị")
        
        valid = ['undefined', 'pixelsperinch', 'pixelspercentimeter']
        unit = Validator.validate_enum(v, valid, "units")
        img.units = unit

    @staticmethod
    def _cmd_depth(img, v):
        # Độ sâu bit màu: 8, 16, 32
        if not v:
            raise ValidationError("depth: thiếu giá trị")
        
        depth = Validator.validate_positive_int(v, "depth")
        if depth not in [1, 8, 16, 32]:
            raise ValidationError("depth: giá trị phải là 1, 8, 16 hoặc 32")
        img.depth = depth

    @staticmethod
    def _cmd_strip(img, v):
        # Xóa toàn bộ profile, comment, EXIF để giảm dung lượng
        img.strip()

    @staticmethod
    def _cmd_virtual_pixel(img, v):
        # Xử lý biên ảnh: background, dither, edge, mirror, random, tile, transparent, etc.
        if not v:
            raise ValidationError("virtual-pixel: thiếu giá trị")
        
        valid = ['background', 'dither', 'edge', 'mirror', 'random', 'tile', 'transparent']
        method = Validator.validate_enum(v, valid, "virtual-pixel")
        img.virtual_pixel = method

    @staticmethod
    def _cmd_compress(img, v):
        # JPEG, LZW, ZIP, None...
        if not v:
            raise ValidationError("compress: thiếu phương thức")
        
        valid = ['none', 'jpeg', 'lzw', 'zip', 'rle', 'bzip']
        method = Validator.validate_enum(v, valid, "compress")
        img.compression = method

    @staticmethod
    def _cmd_format(img, v):
        """
        Convert output format (Fix: Dùng ValidationError thay vì print)
        Ví dụ: -format jpg, -format png, -format webp
        """
        if not v:
            raise ValidationError("format: Thiếu định dạng (VD: jpg, png, webp)")
        
        # Danh sách format phổ biến để kiểm tra nhanh
        valid_formats = [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
            'webp', 'ico', 'psd', 'svg', 'pdf',
            'dng', 'cr2', 'nef', 'arw', 'orf',
            'heic', 'avif', 'jp2', 'jxl', 'pcx', 'tga', 'exr', 'hdr'
        ]
        
        fmt = v.lower().strip()
        
        if fmt not in valid_formats:
            # Cảnh báo định dạng lạ (có thể vẫn chạy nếu máy có codec, nhưng báo lỗi cho chắc)
            raise ValidationError(f"format: Định dạng '{v}' không phổ biến hoặc không hỗ trợ")

        # Map alias (Wand/ImageMagick đôi khi cần tên chuẩn)
        alias_map = {
            'jpg': 'jpeg',
            'tif': 'tiff'
        }
        final_fmt = alias_map.get(fmt, fmt)
        
        try:
            img.format = final_fmt
        except Exception as e:
            raise ValidationError(f"format: Không thể chuyển sang định dạng '{fmt}': {e}")

    @classmethod
    def get_map(cls):
        return {
            'quality': cls._cmd_quality,
            'density': cls._cmd_density,
            'units': cls._cmd_units,
            'depth': cls._cmd_depth,
            'strip': cls._cmd_strip,
            'virtual-pixel': cls._cmd_virtual_pixel,
            'compress': cls._cmd_compress,
            'format': cls._cmd_format,
        }