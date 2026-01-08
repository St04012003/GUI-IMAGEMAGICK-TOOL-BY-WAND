# core.py

import re
from typing import List, Tuple, Optional
from collections import OrderedDict
from wand.image import Image as WandImage
from PyQt5.QtGui import QImage

from config import CONFIG
from utils import SafeParse, handle_errors


# ===========
# VALIDATION
# ===========
class ValidationError(Exception):
    """Custom exception cho validation errors"""
    pass


class Validator:
    """Helper class cho các hàm validation chung"""
    
    @staticmethod
    def validate_positive_int(value: str, param_name: str, allow_zero: bool = False) -> int:
        """Validate số nguyên dương"""
        try:
            val = SafeParse.int_val(value, -1)
            if val < 0 or (not allow_zero and val == 0):
                raise ValidationError(f"{param_name} phải là số nguyên {'không âm' if allow_zero else 'dương'}")
            return val
        except:
            raise ValidationError(f"{param_name} không hợp lệ: {value}")
    
    @staticmethod
    def validate_float(value: str, param_name: str, min_val: float = None, max_val: float = None) -> float:
        """Validate số thực trong khoảng"""
        try:
            val = SafeParse.float_val(value)
            if min_val is not None and val < min_val:
                raise ValidationError(f"{param_name} phải >= {min_val}")
            if max_val is not None and val > max_val:
                raise ValidationError(f"{param_name} phải <= {max_val}")
            return val
        except ValidationError:
            raise
        except:
            raise ValidationError(f"{param_name} không hợp lệ: {value}")
    
    @staticmethod
    def validate_percentage(value: str, param_name: str) -> float:
        """Validate phần trăm (0-100)"""
        cleaned = value.replace('%', '').strip()
        val = Validator.validate_float(cleaned, param_name, 0, 100)
        return val / 100.0
    
    @staticmethod
    def validate_geometry(value: str, require_positive: bool = True) -> Tuple[int, int, int, int]:
        """Validate geometry string"""
        geo = SafeParse.geometry(value)
        if not geo:
            raise ValidationError(f"Geometry không hợp lệ: {value}")
        
        w, h, x, y = geo
        if require_positive and (w <= 0 and h <= 0):
            raise ValidationError(f"Geometry phải có ít nhất 1 dimension > 0: {value}")
        
        return geo
    
    @staticmethod
    def validate_not_empty(value: str, param_name: str) -> str:
        """Validate string không rỗng"""
        if not value or not value.strip():
            raise ValidationError(f"{param_name} không được để trống")
        return value.strip()
    
    @staticmethod
    def validate_color(value: str) -> str:
        """Validate color string"""
        # Basic validation - ImageMagick sẽ validate chi tiết hơn
        if not value or not value.strip():
            raise ValidationError("Màu không được để trống")
        return value.strip()
    
    @staticmethod
    def validate_enum(value: str, valid_values: List[str], param_name: str) -> str:
        """Validate giá trị trong danh sách cho phép"""
        val = value.lower().strip()
        if val not in valid_values:
            raise ValidationError(f"{param_name} phải là một trong: {', '.join(valid_values)}")
        return val

# ==========================
# CLASS QUẢN LÝ CACHE (LRU)
# ==========================
class ImageCache:    
    # Quản lý bộ nhớ đệm (Cache) theo cơ chế LRU (Least Recently Used)
    def __init__(self, max_size=30):
        self.max_size = max_size # max_size: Số lượng trạng thái lệnh tối đa muốn lưu (VD: 30 lệnh)
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[QImage]:
        # Lấy ảnh từ cache. Nếu có, đưa nó lên đầu danh sách (đánh dấu vừa dùng).
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, image: QImage):
        # Lưu ảnh vào cache. Nếu đầy, xóa cái cũ nhất.
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = image
        
        # Nếu vượt quá giới hạn, xóa item đầu tiên (là cái ít dùng nhất - LRU)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
            
    def clear(self):
        # Xóa sạch cache (Dùng khi nạp ảnh gốc mới)
        self.cache.clear()


# ================================
# CORE LOGIC (COMMAND PARSER)
# ================================


    
# ------ CommandParser ------#

class CommandParser:
    """
    Trình phân tích cú pháp lệnh. 
    Chuyển đổi chuỗi lệnh text (VD: '-resize 50%') thành hàm gọi API của Wand.
    """

    """
    ImageMagick Command Parser (Ultimate Version)
    Hỗ trợ hầu hết các lệnh xử lý ảnh đơn (Single Image Operators) và Image Settings.
    Updated based on: https://imagemagick.org/script/command-line-processing.php
    """

    @staticmethod
    def parse(command_string: str) -> List[Tuple[str, Optional[str]]]:
        # Tách chuỗi lệnh thành danh sách các cặp (lệnh, giá trị)
        # Chuẩn hóa: thêm khoảng trắng quanh dấu phẩy, xóa khoảng trắng thừa
        cleaned_cmd = re.sub(r',\s+', ',', command_string.strip())
        tokens = cleaned_cmd.split()
        
        operations = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Kiểm tra xem token có phải là lệnh (bắt đầu bằng '-', không phải số âm)
            if token.startswith('-') and len(token) > 1 and not (token[1].isdigit() or (token[1] == '.' and len(token) > 2)):
                cmd = token[1:].lower()
                value = None
                
                # Kiểm tra token tiếp theo có phải là giá trị không
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    is_next_command = (
                        next_token.startswith('-') and 
                        len(next_token) > 1 and 
                        not (next_token[1].isdigit() or (next_token[1] == '.' and len(next_token) > 2))
                    )
                    if not is_next_command:
                        value = next_token
                        i += 1
                
                operations.append((cmd, value))
            i += 1
        
        return operations

    # --- Các hàm xử lý ảnh cụ thể (Wrapper cho Wand) ---
    
    # 1. GEOMETRY & TRANSFORM (Biến đổi hình học)
    @staticmethod
    def _cmd_resize(img, v):
        """Resize with full validation"""
        if not v:
            raise ValidationError("resize: thiếu tham số (VD: 50%, 800x600)")
        
        try:
            if '%' in v:
                percent = Validator.validate_percentage(v, "resize percentage")
                if percent <= 0:
                    raise ValidationError("resize: phần trăm phải > 0")
                new_w = int(img.width * percent)
                new_h = int(img.height * percent)
                if new_w < 1 or new_h < 1:
                    raise ValidationError("resize: kích thước kết quả quá nhỏ")
                img.resize(new_w, new_h)
            else:
                w, h, _, _ = Validator.validate_geometry(v, require_positive=True)
                
                # Auto-calculate missing dimension
                if w > 0 and h == 0:
                    h = int(w * img.height / img.width) if img.width > 0 else img.height
                if h > 0 and w == 0:
                    w = int(h * img.width / img.height) if img.height > 0 else img.width
                
                if w < 1 or h < 1:
                    raise ValidationError("resize: kích thước phải >= 1 pixel")
                
                img.resize(w, h)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"resize: lỗi không xác định - {e}")

    @staticmethod
    def _cmd_scale(img, v):
        """Scale with validation"""
        if not v:
            raise ValidationError("scale: thiếu tham số")
        
        if '%' in v:
            percent = Validator.validate_percentage(v, "scale percentage")
            if percent <= 0:
                raise ValidationError("scale: phần trăm phải > 0")
            img.scale(int(img.width * percent), int(img.height * percent))
        else:
            w, h, _, _ = Validator.validate_geometry(v)
            if w < 1 or h < 1:
                raise ValidationError("scale: kích thước phải >= 1 pixel")
            img.scale(w, h)

    @staticmethod
    def _cmd_sample(img, v):
        """Sample with validation"""
        if not v:
            raise ValidationError("sample: thiếu tham số")
        
        if '%' in v:
            percent = Validator.validate_percentage(v, "sample percentage")
            if percent <= 0:
                raise ValidationError("sample: phần trăm phải > 0")
            img.sample(int(img.width * percent), int(img.height * percent))
        else:
            w, h, _, _ = Validator.validate_geometry(v)
            if w < 1 or h < 1:
                raise ValidationError("sample: kích thước phải >= 1 pixel")
            img.sample(w, h)

    @staticmethod
    def _cmd_liquid_rescale(img, v):
        """Liquid rescale with validation"""
        if not v:
            raise ValidationError("liquid-rescale: thiếu tham số geometry")
        
        w, h, _, _ = Validator.validate_geometry(v)
        if w < 1 or h < 1:
            raise ValidationError("liquid-rescale: kích thước phải >= 1 pixel")
        img.liquid_rescale(w, h)

    @staticmethod
    def _cmd_extent(img, v):
        """Extent with validation"""
        if not v:
            raise ValidationError("extent: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        final_w = w if w > 0 else img.width
        final_h = h if h > 0 else img.height
        
        if final_w < 1 or final_h < 1:
            raise ValidationError("extent: kích thước phải >= 1 pixel")
        
        img.extent(width=final_w, height=final_h, x=x, y=y)

    @staticmethod
    def _cmd_repage(img, v):
        """Repage with validation"""
        if not v:
            img.page = (0, 0, 0, 0)
        else:
            geo = Validator.validate_geometry(v, require_positive=False)
            img.page = geo

    @staticmethod
    def _cmd_crop(img, v):
        """Crop with validation"""
        if not v:
            raise ValidationError("crop: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        
        # Validate crop area
        if x < 0 or y < 0:
            raise ValidationError("crop: tọa độ x, y phải >= 0")
        if x >= img.width or y >= img.height:
            raise ValidationError("crop: tọa độ nằm ngoài ảnh")
        
        right = x + w if w > 0 else img.width
        bottom = y + h if h > 0 else img.height
        
        if right > img.width or bottom > img.height:
            raise ValidationError("crop: vùng crop vượt quá kích thước ảnh")
        
        img.crop(left=x, top=y, right=right, bottom=bottom)

    @staticmethod
    def _cmd_rotate(img, v):
        """Rotate with validation"""
        if not v:
            raise ValidationError("rotate: thiếu góc xoay")
        
        degree = Validator.validate_float(v, "rotate angle", -360, 360)
        img.rotate(degree=degree)

    @staticmethod
    def _cmd_auto_orient(img, v):
        """Auto orient - không cần validation"""
        img.auto_orient()

    @staticmethod
    def _cmd_deskew(img, v):
        """Deskew with validation"""
        threshold = 0.4
        if v:
            threshold = Validator.validate_float(v, "deskew threshold", 0, 1)
        img.deskew(threshold=threshold)

    @staticmethod
    def _cmd_shear(img, v):
        """Shear with validation"""
        if not v:
            raise ValidationError("shear: thiếu tham số (VD: 30 hoặc 30x45)")
        
        if 'x' in v.lower():
            parts = v.lower().split('x')
            if len(parts) != 2:
                raise ValidationError("shear: format phải là XxY (VD: 30x45)")
            x = Validator.validate_float(parts[0], "shear X", -89, 89)
            y = Validator.validate_float(parts[1], "shear Y", -89, 89)
        else:
            x = y = Validator.validate_float(v, "shear angle", -89, 89)
        
        img.shear(background=img.background_color, x=x, y=y)

    @staticmethod
    def _cmd_flip(img, v): 
        img.flip()       # Lật dọc

    @staticmethod
    def _cmd_flop(img, v): 
        img.flop()       # Lật ngang

    @staticmethod
    def _cmd_transpose(img, v): 
        img.transpose()

    @staticmethod
    def _cmd_transverse(img, v): 
        img.transverse()

    @staticmethod
    def _cmd_trim(img, v): 
        img.trim(fuzz=0) # Cắt bỏ viền màu đồng nhất
   
    # 2. IMAGE SETTINGS & METADATA (Cài đặt & Dữ liệu ảnh) - [NEW]
    
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
        Convert output format
        Ví dụ: -format jpg, -format png, -format webp
        """
        if not v:
            print("⚠️ -format: Thiếu định dạng (VD: jpg, png, webp)")
            return
        
        # Danh sách format phổ biến
        valid_formats = [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
            'webp', 'ico', 'psd', 'svg', 'pdf',
            'dng', 'cr2', 'nef', 'arw', 'orf',
            'heic', 'avif', 'jp2', 'jxl', 'pcx', 'tga', 'exr', 'hdr'
        ]
        
        fmt = v.lower().strip()
        
        if fmt not in valid_formats:
            print(f"⚠️ -format: Định dạng '{v}' chưa được hỗ trợ hoặc không hợp lệ")
            print(f"   Các format được hỗ trợ: {', '.join(valid_formats[:15])}...")
            return
        
        # Map alias
        if fmt == 'jpg':
            fmt = 'jpeg'
        elif fmt == 'tif':
            fmt = 'tiff'
        
        try:
            img.format = fmt
        except Exception as e:
            print(f"⚠️ -format: Không thể chuyển sang định dạng '{fmt}': {e}")

    # 3. COLOR & CHANNEL (Màu sắc & Kênh màu)

    @staticmethod
    def _cmd_colorspace(img, v):
        # gray, rgb, cmyk, srgb, hsl, hsb...
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
        # grayscale, bilevel, truecolor, palette...
        if not v:
            raise ValidationError("type: thiếu giá trị")
        
        valid = ['bilevel', 'grayscale', 'palette', 'truecolor', 'colorseparation', 'optimize']
        img_type = Validator.validate_enum(v, valid, "type")
        img.type = img_type
        
    @staticmethod
    def _cmd_monochrome(img, v):
        # Chuyển thành ảnh đen trắng 2 màu (1-bit dithered)
        img.type = 'bilevel'

    @staticmethod
    def _cmd_alpha(img, v):
        # activate, deactivate, set, opaque, transparent...
        if not v:
            raise ValidationError("alpha: thiếu mode (on/off/remove)")
        
        valid = ['on', 'off', 'activate', 'deactivate', 'remove', 'set']
        mode = Validator.validate_enum(v, valid, "alpha")
        
        if mode in ['off', 'deactivate']:
            img.alpha_channel = False
        elif mode in ['on', 'activate']:
            img.alpha_channel = True
        elif mode == 'remove':
            img.alpha_channel = 'remove'

    @staticmethod
    def _cmd_background(img, v):
        if not v:
            raise ValidationError("background: thiếu màu")
        
        color = Validator.validate_color(v)
        img.background_color = color

    @staticmethod
    def _cmd_transparent(img, v):
        # Biến một màu thành trong suốt. VD: -transparent white
        if not v:
            raise ValidationError("transparent: thiếu màu")
        
        color = Validator.validate_color(v)
        img.transparent_color(color=color, alpha=0.0)


    @staticmethod
    def _cmd_brightness_contrast(img, v):
        # brightness x contrast (VD: 10x20)
        if not v:
            raise ValidationError("brightness-contrast: thiếu giá trị (VD: 10x20)")
        
        parts = re.split(r'[x,]', v)
        if len(parts) < 1:
            raise ValidationError("brightness-contrast: format không hợp lệ")
        
        b = Validator.validate_float(parts[0], "brightness", -100, 100)
        c = 0 if len(parts) < 2 else Validator.validate_float(parts[1], "contrast", -100, 100)
        img.brightness_contrast(brightness=b, contrast=c)

    @staticmethod
    def _cmd_level(img, v):
        # black_point, white_point, gamma
        if not v:
            raise ValidationError("level: thiếu giá trị")
        
        parts = v.replace('%', '').split(',')
        b = Validator.validate_float(parts[0], "black point", 0, 100) / 100.0
        w = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "white point", 0, 100) / 100.0
        g = 1.0 if len(parts) < 3 else Validator.validate_float(parts[2], "gamma", 0.1, 10)
        
        if b >= w:
            raise ValidationError("level: black point phải < white point")
        
        img.level(black=b, white=w, gamma=g)

    @staticmethod
    def _cmd_threshold(img, v):
        # Chuyển đen trắng dựa trên ngưỡng (VD: 50%)
        if not v:
            raise ValidationError("threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "threshold")
        img.threshold(threshold=t)
            
    @staticmethod
    def _cmd_black_threshold(img, v):
        # Buộc các màu dưới ngưỡng thành màu đen
        if not v:
            raise ValidationError("black-threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "black-threshold")
        img.black_threshold(threshold=t)

    @staticmethod
    def _cmd_white_threshold(img, v):
        # Buộc các màu trên ngưỡng thành màu trắng
        if not v:
            raise ValidationError("white-threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "white-threshold")
        img.white_threshold(threshold=t)

    @staticmethod
    def _cmd_gamma(img, v):
        # Gamma correction
        if not v:
            raise ValidationError("gamma: thiếu giá trị")
        
        gamma = Validator.validate_float(v, "gamma", 0.1, 10)
        img.gamma(gamma)

    @staticmethod
    def _cmd_auto_level(img, v): 
        img.auto_level()

    @staticmethod
    def _cmd_auto_gamma(img, v): 
        img.auto_gamma()

    @staticmethod
    def _cmd_normalize(img, v): 
        img.normalize()

    @staticmethod
    def _cmd_equalize(img, v): 
        img.equalize()

    @staticmethod
    def _cmd_negate(img, v): 
        img.negate()

    @staticmethod
    def _cmd_grayscale(img, v): 
        img.type = 'grayscale'

    @staticmethod
    def _cmd_modulate(img, v):
        # brightness, saturation, hue (100,100,100 is default)
        if not v:
            raise ValidationError("modulate: thiếu giá trị (brightness,saturation,hue)")
        
        parts = v.split(',')
        b = Validator.validate_float(parts[0], "brightness", 0, 200)
        s = 100 if len(parts) < 2 else Validator.validate_float(parts[1], "saturation", 0, 200)
        h = 100 if len(parts) < 3 else Validator.validate_float(parts[2], "hue", 0, 200)
        
        img.modulate(brightness=b, saturation=s, hue=h)

    @staticmethod
    def _cmd_sigmoidal_contrast(img, v):
        # contrast x midpoint (VD: 3x50%)
        if not v:
            raise ValidationError("sigmoidal-contrast: thiếu giá trị")
        
        parts = re.split(r'[x,]', v.replace('%',''))
        c = Validator.validate_float(parts[0], "contrast", 0, 20)
        m = 0.5 if len(parts) < 2 else Validator.validate_float(parts[1], "midpoint", 0, 100) / 100.0
        
        img.sigmoidal_contrast(strength=c, midpoint=m)


    @staticmethod
    def _cmd_colorize(img, v):
        # Tô màu phủ lên ảnh: color, alpha (VD: red,50)
        if not v:
            raise ValidationError("colorize: thiếu màu")
        
        parts = v.split(',')
        color = Validator.validate_color(parts[0])
        alpha = parts[1] if len(parts) > 1 else "100%"
        
        img.colorize(color=color, alpha=alpha)

    # 4. FILTERS & ENHANCE (Lọc & Tăng cường)
    
    @staticmethod
    def _cmd_blur(img, v):
        # radius x sigma
        if not v:
            raise ValidationError("blur: thiếu tham số (radius hoặc radiusxsigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "blur radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "blur sigma", 0, 100)
        
        img.blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_gaussian_blur(img, v):
        if not v:
            raise ValidationError("gaussian-blur: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.gaussian_blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_sharpen(img, v):
        if not v:
            raise ValidationError("sharpen: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.sharpen(radius=r, sigma=s)

    @staticmethod
    def _cmd_unsharp(img, v):
        # radius x sigma + amount + threshold
        if not v:
            raise ValidationError("unsharp: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        parts = [x for x in parts if x]
        
        r = Validator.validate_float(parts[0], "radius", 0, 100) if len(parts) > 0 else 0
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        a = 1.0 if len(parts) < 3 else Validator.validate_float(parts[2], "amount", 0, 10)
        t = 0.05 if len(parts) < 4 else Validator.validate_float(parts[3], "threshold", 0, 1)
        
        img.unsharp_mask(radius=r, sigma=s, amount=a, threshold=t)

    @staticmethod
    def _cmd_despeckle(img, v): 
        img.despeckle()
    @staticmethod
    def _cmd_reduce_noise(img, v): 
        img.despeckle()
    @staticmethod
    def _cmd_enhance(img, v): 
        img.enhance() # Digital filter to improve quality
    
    @staticmethod
    def _cmd_noise(img, v):
        # Add noise: gaussian, impulse, laplacian, poisson, uniform...
        if not v:
            raise ValidationError("noise: thiếu loại noise")
        
        valid = ['gaussian', 'impulse', 'laplacian', 'poisson', 'uniform', 'random']
        noise_type = Validator.validate_enum(v, valid, "noise type")
        img.noise(noise_type, attenuate=1.0)

    @staticmethod
    def _cmd_median(img, v):
        # radius
        radius = 1
        if v:
            radius = Validator.validate_float(v, "median radius", 0, 50)
        img.median_filter(radius=radius)

    @staticmethod
    def _cmd_kuwahara(img, v):
        # radius x sigma (Edge preserving smooth)
        if not v:
            raise ValidationError("kuwahara: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 0.5 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 10)
        
        img.kuwahara(radius=r, sigma=s)
    
    # 5. ARTISTIC & EFFECTS (Hiệu ứng nghệ thuật)
    
    @staticmethod
    def _cmd_sepia(img, v):
        threshold = 0.8
        if v:
            threshold = Validator.validate_percentage(v, "sepia threshold")
        img.sepia_tone(threshold=threshold)

    @staticmethod
    def _cmd_solarize(img, v):
        threshold = 0.5
        if v:
            threshold = Validator.validate_percentage(v, "solarize threshold")
        img.solarize(threshold=threshold)

    @staticmethod
    def _cmd_posterize(img, v):
        if not v:
            raise ValidationError("posterize: thiếu số levels")
        
        levels = Validator.validate_positive_int(v, "posterize levels")
        if levels > 256:
            raise ValidationError("posterize: levels phải <= 256")
        img.posterize(levels=levels)

    @staticmethod
    def _cmd_oil_paint(img, v):
        # radius
        radius = 3
        if v:
            radius = Validator.validate_float(v, "oil paint radius", 0, 50)
        img.oil_paint(radius=radius)

    @staticmethod
    def _cmd_charcoal(img, v):
        # radius x sigma
        if not v:
            raise ValidationError("charcoal: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        
        img.charcoal(radius=r, sigma=s)

    @staticmethod
    def _cmd_sketch(img, v):
        # radius x sigma + angle
        if not v:
            raise ValidationError("sketch: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        a = 0 if len(parts) < 3 else Validator.validate_float(parts[2], "angle", 0, 360)
        
        img.sketch(radius=r, sigma=s, angle=a)

    @staticmethod
    def _cmd_swirl(img, v):
        if not v:
            raise ValidationError("swirl: thiếu góc xoáy")
        
        degree = Validator.validate_float(v, "swirl degree", -360, 360)
        img.swirl(degree=degree)

    @staticmethod
    def _cmd_wave(img, v):
        # amplitude x wavelength
        if not v:
            raise ValidationError("wave: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        amplitude = Validator.validate_float(parts[0], "amplitude", 0, 1000)
        wavelength = amplitude * 2 if len(parts) < 2 else Validator.validate_float(parts[1], "wavelength", 0, 1000)
        
        img.wave(amplitude=amplitude, wave_length=wavelength)

    @staticmethod
    def _cmd_implode(img, v):
        # amount (0-1)
        amount = 0.5
        if v:
            amount = Validator.validate_float(v, "implode amount", 0, 1)
        img.implode(amount=amount)

    @staticmethod
    def _cmd_vignette(img, v):
        # radius x sigma + x + y (Làm tối góc ảnh)
        if not v:
            raise ValidationError("vignette: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 500)
        s = 10 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        x = 0 if len(parts) < 3 else Validator.validate_positive_int(parts[2], "x offset", allow_zero=True)
        y = 0 if len(parts) < 4 else Validator.validate_positive_int(parts[3], "y offset", allow_zero=True)
        
        img.vignette(radius=r, sigma=s, x=x, y=y)

    @staticmethod
    def _cmd_polaroid(img, v):
        # angle
        angle = 0
        if v:
            angle = Validator.validate_float(v, "polaroid angle", -360, 360)
        img.polaroid(angle=angle)

    @staticmethod
    def _cmd_shadow(img, v):
        # opacity x sigma + x + y (Tạo bóng đổ)
        if not v:
            raise ValidationError("shadow: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        opacity = Validator.validate_float(parts[0], "opacity", 0, 100)
        sigma = 3 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        x = 5 if len(parts) < 3 else Validator.validate_positive_int(parts[2], "x offset", allow_zero=True)
        y = 5 if len(parts) < 4 else Validator.validate_positive_int(parts[3], "y offset", allow_zero=True)
        
        img.shadow(alpha=opacity, sigma=sigma, x=x, y=y)
            
    @staticmethod
    def _cmd_blue_shift(img, v):
        # Giả lập cảnh ban đêm
        factor = 1.5
        if v:
            factor = Validator.validate_float(v, "blue shift factor", 0.1, 10)
        img.blue_shift(factor=factor)

    # 6. DECORATION & BORDER (Trang trí)

    @staticmethod
    def _cmd_border(img, v):
        # width x height (màu lấy từ -background hoặc mặc định)
        if not v:
            raise ValidationError("border: thiếu kích thước")
        
        w, h, _, _ = Validator.validate_geometry(v)
        if w < 0 or h < 0:
            raise ValidationError("border: kích thước không được âm")
        
        color = img.background_color or "white"
        img.border(color=color, width=w, height=h)

    @staticmethod
    def _cmd_frame(img, v):
        # width x height + inner + outer (Tạo khung 3D)
        if not v:
            raise ValidationError("frame: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        w = Validator.validate_positive_int(parts[0], "frame width", allow_zero=True)
        h = w if len(parts) < 2 else Validator.validate_positive_int(parts[1], "frame height", allow_zero=True)
        inner = 0 if len(parts) < 3 else Validator.validate_positive_int(parts[2], "inner bevel", allow_zero=True)
        outer = 0 if len(parts) < 4 else Validator.validate_positive_int(parts[3], "outer bevel", allow_zero=True)
        
        color = img.matte_color or "gray"
        img.frame(matte=color, width=w, height=h, inner_bevel=inner, outer_bevel=outer)

    # 7. EDGE & MORPHOLOGY (Cạnh & Hình thái học)

    @staticmethod
    def _cmd_edge(img, v):
        radius = 1
        if v:
            radius = Validator.validate_float(v, "edge radius", 0, 50)
        img.edge(radius=radius)

    @staticmethod
    def _cmd_canny(img, v):
        # radius x sigma + lower% + upper%
        if not v:
            raise ValidationError("canny: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        parts = [x for x in parts if x]
        
        r = Validator.validate_float(parts[0], "radius", 0, 50) if len(parts) > 0 else 0
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        lower = 0.1 if len(parts) < 3 else Validator.validate_float(parts[2], "lower %", 0, 100) / 100.0
        upper = 0.3 if len(parts) < 4 else Validator.validate_float(parts[3], "upper %", 0, 100) / 100.0
        
        if lower >= upper:
            raise ValidationError("canny: lower threshold phải < upper threshold")
        
        img.canny(radius=r, sigma=s, lower_percent=lower, upper_percent=upper)
            
    @staticmethod
    def _cmd_morphology(img, v):
        # Method:Kernel (VD: Dilate:Disk:2)
        if not v:
            raise ValidationError("morphology: thiếu tham số (Method:Kernel)")
        
        parts = v.split(':')
        if len(parts) < 1:
            raise ValidationError("morphology: format phải là Method:Kernel")
        
        method = Validator.validate_not_empty(parts[0], "morphology method")
        kernel = ":".join(parts[1:]) if len(parts) > 1 else 'Disk'
        
        try:
            img.morphology(method=method, kernel=kernel)
        except Exception as e:
            raise ValidationError(f"morphology: lỗi - {e}")

    # ----------- DISPATCHER MAPPING -----------

    DISPATCH = {
        # Geometry
        'resize': _cmd_resize.__func__,
        'scale': _cmd_scale.__func__,
        'sample': _cmd_sample.__func__,
        'resample': _cmd_sample.__func__, # Wand gọi là sample hoặc resize, alias cho tiện
        'liquid-rescale': _cmd_liquid_rescale.__func__,
        'crop': _cmd_crop.__func__,
        'extent': _cmd_extent.__func__,
        'repage': _cmd_repage.__func__, # NEW
        'rotate': _cmd_rotate.__func__,
        'auto-orient': _cmd_auto_orient.__func__, # NEW
        'flip': _cmd_flip.__func__,
        'flop': _cmd_flop.__func__,
        'transpose': _cmd_transpose.__func__,
        'transverse': _cmd_transverse.__func__,
        'trim': _cmd_trim.__func__,
        'deskew': _cmd_deskew.__func__,
        'shear': _cmd_shear.__func__,

        # Image Settings (NEW)
        'quality': _cmd_quality.__func__,
        'density': _cmd_density.__func__,
        'units': _cmd_units.__func__,
        'depth': _cmd_depth.__func__,
        'strip': _cmd_strip.__func__,
        'virtual-pixel': _cmd_virtual_pixel.__func__,
        'compress': _cmd_compress.__func__,
        'format': _cmd_format.__func__,

        # Color
        'grayscale': _cmd_grayscale.__func__,
        'monochrome': _cmd_monochrome.__func__, # NEW
        'colorspace': _cmd_colorspace.__func__,
        'type': _cmd_type.__func__,
        'alpha': _cmd_alpha.__func__,
        'background': _cmd_background.__func__,
        'transparent': _cmd_transparent.__func__,
        'negate': _cmd_negate.__func__,
        'level': _cmd_level.__func__,
        'auto-level': _cmd_auto_level.__func__,
        'auto-gamma': _cmd_auto_gamma.__func__,
        'brightness-contrast': _cmd_brightness_contrast.__func__,
        'modulate': _cmd_modulate.__func__,
        'normalize': _cmd_normalize.__func__,
        'equalize': _cmd_equalize.__func__,
        'gamma': _cmd_gamma.__func__, # NEW
        'threshold': _cmd_threshold.__func__, # NEW
        'black-threshold': _cmd_black_threshold.__func__, # NEW
        'white-threshold': _cmd_white_threshold.__func__, # NEW
        'sigmoidal-contrast': _cmd_sigmoidal_contrast.__func__,
        'colorize': _cmd_colorize.__func__,
        'blue-shift': _cmd_blue_shift.__func__,

        # Filters
        'blur': _cmd_blur.__func__,
        'gaussian-blur': _cmd_gaussian_blur.__func__,
        'sharpen': _cmd_sharpen.__func__,
        'unsharp': _cmd_unsharp.__func__,
        'despeckle': _cmd_despeckle.__func__,
        'reduce-noise': _cmd_reduce_noise.__func__,
        'noise': _cmd_noise.__func__,
        'median': _cmd_median.__func__,
        'enhance': _cmd_enhance.__func__,
        'kuwahara': _cmd_kuwahara.__func__,

        # Artistic
        'sepia-tone': _cmd_sepia.__func__,
        'sepia': _cmd_sepia.__func__, # Alias
        'solarize': _cmd_solarize.__func__,
        'posterize': _cmd_posterize.__func__,
        'oil-paint': _cmd_oil_paint.__func__,
        'charcoal': _cmd_charcoal.__func__,
        'sketch': _cmd_sketch.__func__,
        'swirl': _cmd_swirl.__func__,
        'wave': _cmd_wave.__func__,
        'implode': _cmd_implode.__func__,
        'vignette': _cmd_vignette.__func__,
        'polaroid': _cmd_polaroid.__func__,
        'shadow': _cmd_shadow.__func__,

        # Decor & Edge
        'border': _cmd_border.__func__,
        'frame': _cmd_frame.__func__,
        'edge': _cmd_edge.__func__,
        'canny': _cmd_canny.__func__,
        'morphology': _cmd_morphology.__func__,
    }

    @classmethod
    def _init_config_commands(cls):
        """Tự động điền danh sách lệnh vào Config để Autocomplete"""
        CONFIG.commands = sorted([f"-{cmd}" for cmd in cls.DISPATCH.keys()])

    @classmethod
    @handle_errors()
    def apply_commands(cls, img, operations: List[Tuple[str, Optional[str]]]):
        """Áp dụng danh sách lệnh lên đối tượng ảnh Wand"""
        for cmd, value in operations:
            handler = cls.DISPATCH.get(cmd)
            if handler:
                try:
                    handler(img, value)
                except Exception as e:
                    print(f"⚠️ Lỗi khi thực thi lệnh '-{cmd} {value}': {e}")
            else:
                print(f"⚠️ Lệnh không xác định hoặc chưa hỗ trợ: -{cmd}")
        return img

# Khởi chạy cập nhật Config ngay khi class được định nghĩa
CommandParser._init_config_commands()