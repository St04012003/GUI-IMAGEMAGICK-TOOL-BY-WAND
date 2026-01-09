# core/validator.py
from typing import List, Tuple, Optional
from utils import SafeParse

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
