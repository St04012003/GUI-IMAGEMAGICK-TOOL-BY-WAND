# core/cmd_edge.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# =============================================
# 7. EDGE & MORPHOLOGY (Cạnh & Hình thái học)
# =============================================
class EdgeCommands(BaseCommand):
    @staticmethod
    def _cmd_edge(img, v):
        """
        Làm nổi bật cạnh (Simple Edge Detect).
        Tham số: Radius (Độ dày cạnh).
        """
        radius = 1
        if v:
            radius = Validator.validate_float(v, "edge radius", 0, 50)
        img.edge(radius=radius)

    @staticmethod
    def _cmd_canny(img, v):
        """
        Dò cạnh thuật toán Canny (Canny Edge Detect).
        Cú pháp: Radius x Sigma + Lower% + Upper%. (VD: 0x1+10%+30%).
        """
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
        """
        Các phép toán hình thái học (Morphology).
        Cú pháp: Method:Kernel. (VD: Dilate:Disk, Erode:Square, Close:Diamond).
        """
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
    
    @staticmethod
    def _cmd_shade(img, v):
        """
        Tạo hiệu ứng chạm khắc nổi 3D (Shade).
        Cú pháp: Azimuth x Elevation. (VD: 30x30).
        Giả lập nguồn sáng chiếu vào ảnh để tạo khối.
        """
        azimuth = 30.0
        elevation = 30.0
        
        if v:
            parts = re.split(r'[x,]', v)
            azimuth = Validator.validate_float(parts[0], "azimuth", 0, 360)
            elevation = 30.0 if len(parts) < 2 else Validator.validate_float(parts[1], "elevation", 0, 180)
            
        # gray=True để tạo hiệu ứng chạm khắc chuẩn (loại bỏ màu gốc)
        img.shade(gray=True, azimuth=azimuth, elevation=elevation)

    @staticmethod
    def _cmd_dilate(img, v):
        """
        Làm dày vùng sáng (Morphology Dilate).
        Tham số: Kernel. (VD: Disk, Square, Diamond). Mặc định: Disk.
        Hữu ích để nối liền các nét đứt đoạn.
        """
        kernel = v if v else 'Disk'
        img.morphology(method='dilate', kernel=kernel)

    @staticmethod
    def _cmd_erode(img, v):
        """
        Làm mỏng vùng sáng (Morphology Erode).
        Tham số: Kernel. (VD: Disk, Square). Mặc định: Disk.
        Hữu ích để loại bỏ các chi tiết thừa nhỏ.
        """
        kernel = v if v else 'Disk'
        img.morphology(method='erode', kernel=kernel)

    @staticmethod
    def _cmd_opening(img, v):
        """
        Khử nhiễu sáng trên nền tối (Morphology Open).
        Là sự kết hợp của Erode -> Dilate. 
        Tham số: Kernel (VD: Disk).
        """
        kernel = v if v else 'Disk'
        img.morphology(method='open', kernel=kernel)

    @staticmethod
    def _cmd_closing(img, v):
        """
        Khử nhiễu tối trên nền sáng (Morphology Close).
        Là sự kết hợp của Dilate -> Erode.
        Tham số: Kernel (VD: Disk).
        """
        kernel = v if v else 'Disk'
        img.morphology(method='close', kernel=kernel)