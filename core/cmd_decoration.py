# core/cmd_ decoration.py
import re
from .validator import Validator, ValidationError

# 6. DECORATION & BORDER (Trang trí)

class DecorationCommands:
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

    @classmethod
    def get_map(cls):
        return {
            'border': cls._cmd_border,
            'frame': cls._cmd_frame,    
            }