# utils/parsers.py
import re
from typing import Optional, Tuple

# ========================================================
# SAFE PARSE UTILITIES
# ========================================================
class SafeParse:
    """Class tiện ích để parse dữ liệu từ input người dùng an toàn hơn"""

    @staticmethod
    def float_val(val, default=0.0):
        """Chuyển chuỗi thành số thực, xử lý cả trường hợp '50%'"""
        try:
            if isinstance(val, str):
                val = val.replace('%', '').strip()
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def int_val(val, default=0):
        """Chuyển chuỗi thành số nguyên, có giới hạn min/max của hệ thống"""
        try:
            # Tái sử dụng float_val để xử lý string tốt hơn (VD: "100.5" -> 100)
            result = int(SafeParse.float_val(val, default))
            
            # ✅ FIX: Giới hạn trong phạm vi hợp lý của 32-bit Integer
            # (-2^31 to 2^31-1)
            MAX_INT = 2147483647
            MIN_INT = -2147483648
            
            if result > MAX_INT:
                return MAX_INT
            if result < MIN_INT:
                return MIN_INT
            
            return result
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def geometry(geo_str) -> Optional[Tuple[int, int, int, int]]:
        """
        Parse chuỗi kích thước dạng: 800x600, 800x600+10+20
        Trả về tuple (width, height, x, y)
        """
        if not geo_str:
            return None
        
        # Handle percentage
        if '%' in geo_str:
            return None  # Let caller handle percentage differently
        
        # Regex giải thích:
        # ^             : Bắt đầu chuỗi
        # (\d+)?        : Group 1 - Width (Số, tùy chọn)
        # (?:x(\d+))?   : Group 2 - Height (Chữ 'x' kèm Số, cả cụm này tùy chọn)
        # ([+\-]\d+)?   : Group 3 - X offset (Dấu +/- và số, tùy chọn)
        # ([+\-]\d+)?   : Group 4 - Y offset (Dấu +/- và số, tùy chọn)
        # $             : Kết thúc chuỗi (đảm bảo không có rác)
        pattern = r'^(\d+)?(?:x(\d+))?([+\-]\d+)?([+\-]\d+)?$'

        match = re.match(pattern, geo_str.strip())
        if match:
            w = int(match.group(1)) if match.group(1) else 0
            h = int(match.group(2)) if match.group(2) else 0
            x = int(match.group(3)) if match.group(3) else 0
            y = int(match.group(4)) if match.group(4) else 0

            # Trường hợp string rác không có số nào
            if w == 0 and h == 0 and x == 0 and y == 0:
                return None
        
            return (w, h, x, y)
        return None