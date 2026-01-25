# core/cmd_ decoration.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# ==========================================
# 6. DECORATION & BORDER (Trang trí)
# ==========================================
class DecorationCommands(BaseCommand):
    @staticmethod
    def _cmd_border(img, v):
        """
        Thêm viền đơn sắc xung quanh ảnh (Border).
        Cú pháp: WxH. (Màu lấy từ lệnh -background).
        """
        if not v:
            raise ValidationError("border: thiếu kích thước")
        
        w, h, _, _ = Validator.validate_geometry(v)
        if w < 0 or h < 0:
            raise ValidationError("border: kích thước không được âm")
        
        color = img.background_color or "white"
        img.border(color=color, width=w, height=h)

    @staticmethod
    def _cmd_frame(img, v):
        """
        Thêm khung tranh 3D (Frame).
        Cú pháp: WxH+Inner+Outer. (VD: 10x10+2+2).
        """
        if not v:
            raise ValidationError("frame: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        w = Validator.validate_positive_int(parts[0], "frame width", allow_zero=True)
        h = w if len(parts) < 2 else Validator.validate_positive_int(parts[1], "frame height", allow_zero=True)
        inner = 0 if len(parts) < 3 else Validator.validate_positive_int(parts[2], "inner bevel", allow_zero=True)
        outer = 0 if len(parts) < 4 else Validator.validate_positive_int(parts[3], "outer bevel", allow_zero=True)
        
        color = img.matte_color or "gray"
        img.frame(matte=color, width=w, height=h, inner_bevel=inner, outer_bevel=outer)
    
    @staticmethod
    def _cmd_shave(img, v):
        """
        Cắt bớt viền ảnh (Shave).
        Cú pháp: WxH. (VD: 10x10 - Cắt 10px từ mỗi cạnh).
        """
        if not v:
            raise ValidationError("shave: thiếu kích thước (WxH)")
        
        w, h, _, _ = Validator.validate_geometry(v)
        img.shave(width=w, height=h)

    @staticmethod
    def _cmd_splice(img, v):
        """
        Chèn thêm vùng đệm vào ảnh (Splice).
        Cú pháp: WxH+X+Y. (VD: 0x20+0+0 - Chèn 20px vào đầu ảnh).
        Màu của vùng chèn lấy từ -background.
        """
        if not v:
            raise ValidationError("splice: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        img.splice(width=w, height=h, x=x, y=y)

    @staticmethod
    def _cmd_chop(img, v):
        """
        Cắt bỏ một vùng ảnh (Chop).
        Cú pháp: WxH+X+Y. (VD: 0x20+0+0 - Cắt bỏ 20px đầu ảnh).
        """
        if not v:
            raise ValidationError("chop: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        img.chop(width=w, height=h, x=x, y=y)