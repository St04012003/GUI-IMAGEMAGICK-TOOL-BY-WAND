# core/cmd_geometry.py
import re
from .validator import Validator, ValidationError

# 1. GEOMETRY & TRANSFORM (Biến đổi hình học)

class GeometryCommands: 
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

    @classmethod
    def get_map(cls):
        return {
            'resize': cls._cmd_resize,
            'scale': cls._cmd_scale,
            'sample': cls._cmd_sample,
            'resample': cls._cmd_sample, # Wand gọi là sample hoặc resize, alias cho tiện
            'liquid-rescale': cls._cmd_liquid_rescale,
            'crop': cls._cmd_crop,
            'extent': cls._cmd_extent,
            'repage': cls._cmd_repage, # NEW
            'rotate': cls._cmd_rotate,
            'auto-orient': cls._cmd_auto_orient, # NEW
            'flip': cls._cmd_flip,
            'flop': cls._cmd_flop,
            'transpose': cls._cmd_transpose,
            'transverse': cls._cmd_transverse,
            'trim': cls._cmd_trim,
            'deskew': cls._cmd_deskew,
            'shear': cls._cmd_shear,
            }