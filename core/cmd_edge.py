# core/cmd_edge.py
import re
from .validator import Validator, ValidationError


# 7. EDGE & MORPHOLOGY (Cạnh & Hình thái học)

class EdgeCommands:
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
        
    @classmethod
    def get_map(cls):
        return {
                'edge': cls._cmd_edge,
                'canny': cls._cmd_canny,
                'morphology': cls._cmd_morphology,
                }
            
