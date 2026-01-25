# core/cmd_filters.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# ========================================
# 4. FILTERS & ENHANCE (Lọc & Tăng cường)
# ========================================
class FiltersCommands(BaseCommand):
    @staticmethod
    def _cmd_blur(img, v):
        """
        Làm mờ ảnh cơ bản (Blur).
        Cú pháp: Radius x Sigma. (VD: 0x5, 0x8).
        """
        if not v:
            raise ValidationError("blur: thiếu tham số (radius hoặc radiusxsigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "blur radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "blur sigma", 0, 100)
        
        img.blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_gaussian_blur(img, v):
        """
        Làm mờ Gaussian (Mịn hơn blur thường).
        Cú pháp: Radius x Sigma. (VD: 0x3).
        """
        if not v:
            raise ValidationError("gaussian-blur: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.gaussian_blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_sharpen(img, v):
        """
        Làm sắc nét ảnh (Sharpen).
        Cú pháp: Radius x Sigma. (VD: 0x1).
        """
        if not v:
            raise ValidationError("sharpen: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        
        img.sharpen(radius=r, sigma=s)

    @staticmethod
    def _cmd_unsharp_mask(img, v):
        """
        Làm nét nâng cao (Unsharp Mask).
        Cú pháp: Radius x Sigma + Amount + Threshold.
        """
        if not v:
            raise ValidationError("unsharp-mask: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        a = 1.0 if len(parts) < 3 else Validator.validate_float(parts[2], "amount", 0, 10)
        t = 0.05 if len(parts) < 4 else Validator.validate_float(parts[3], "threshold", 0, 1)
        
        img.unsharp_mask(radius=r, sigma=s, amount=a, threshold=t)

    @staticmethod
    def _cmd_noise(img, v):
        """
        Thêm nhiễu hạt vào ảnh (Add Noise).
        Loại: gaussian, impulse, laplacian, poisson, uniform, random.
        """
        if not v:
            raise ValidationError("noise: thiếu loại noise")
        
        valid = ['gaussian', 'impulse', 'laplacian', 'poisson', 'uniform', 'random']
        noise_type = Validator.validate_enum(v, valid, "noise type")
        img.noise(noise_type, attenuate=1.0)

    @staticmethod
    def _cmd_median(img, v):
        """
        Lọc trung vị (Median Filter).
        Hiệu quả để khử nhiễu muối tiêu (salt & pepper) mà vẫn giữ cạnh.
        """
        radius = 1
        if v:
            radius = Validator.validate_float(v, "median radius", 0, 50)
        size = int(radius * 2 + 1)
        img.statistic('median', width=size, height=size)

    @staticmethod
    def _cmd_kuwahara(img, v):
        """
        Làm mịn bảo toàn cạnh (Kuwahara Filter).
        Tạo hiệu ứng giống tranh vẽ màu nước.
        """
        if not v:
            raise ValidationError("kuwahara: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 0.5 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 10)
        
        img.kuwahara(radius=r, sigma=s)

    @staticmethod
    def _cmd_despeckle(img, v):
        """
        Khử nhiễu đốm nhỏ (Despeckle).
        Giảm nhiễu hạt trong ảnh scan hoặc ảnh nén chất lượng thấp.
        """
        img.despeckle()
    
    @staticmethod
    def _cmd_adaptive_blur(img, v):
        """
        Làm mờ thích ứng (Adaptive Blur).
        Cú pháp: Radius x Sigma. (VD: 0x1).
        Làm mờ vùng phẳng, giữ lại các cạnh sắc nét.
        """
        if not v:
            raise ValidationError("adaptive-blur: thiếu tham số (Radius x Sigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.adaptive_blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_adaptive_sharpen(img, v):
        """
        Làm nét thích ứng (Adaptive Sharpen).
        Cú pháp: Radius x Sigma. (VD: 0x1).
        Tăng độ nét ở cạnh, hạn chế tăng nhiễu ở vùng phẳng.
        """
        if not v:
            raise ValidationError("adaptive-sharpen: thiếu tham số (Radius x Sigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.adaptive_sharpen(radius=r, sigma=s)

    @staticmethod
    def _cmd_enhance(img, v):
        """
        Tự động khử nhiễu và tăng chất lượng (Enhance).
        Giảm nhiễu số (digital noise) mà vẫn giữ chi tiết.
        Lệnh này không cần tham số.
        """
        img.enhance()

    @staticmethod
    def _cmd_statistic(img, v):
        """
        Thay thế pixel bằng giá trị thống kê lân cận (Statistic).
        Cú pháp: Type:WxH. (VD: median:3x3, minimum:3x3).
        Types: gradient, maximum, mean, median, minimum, mode, nonpeak...
        """
        if not v:
            raise ValidationError("statistic: thiếu tham số (Type:WxH)")
            
        parts = v.split(':')
        stat_type = Validator.validate_enum(parts[0], 
            ['gradient', 'maximum', 'mean', 'median', 'minimum', 'mode', 'nonpeak', 'standard_deviation'], 
            "statistic type")
            
        geometry = parts[1] if len(parts) > 1 else "3x3"
        w, h, _, _ = Validator.validate_geometry(geometry)
        
        img.statistic(stat_type, width=w, height=h)
    
    @staticmethod
    def _cmd_mode(img, v):
        """
        Lọc Mode (Lấy màu xuất hiện nhiều nhất).
        Khử nhiễu muối tiêu cực tốt cho truyện tranh mà không làm mờ nét vẽ.
        Tham số: Radius (Mặc định 1).
        """
        radius = 1
        if v:
            radius = Validator.validate_float(v, "mode radius", 0, 50)
        
        # Size kernel phải là số lẻ
        size = int(radius * 2 + 1)
        img.statistic('mode', width=size, height=size)

    @staticmethod
    def _cmd_cca(img, v):
        """
        Phân tích vùng liên thông (Connected Components - CCA).
        Tác dụng: Xóa sạch các hạt bụi/đốm nhỏ hơn diện tích quy định.
        Tham số: Ngưỡng diện tích (VD: 5 -> xóa vùng < 5 pixels).
        """
        if not v:
            raise ValidationError("cca: thiếu tham số area-threshold (VD: 5)")
        
        area = Validator.validate_float(v, "cca area", 0, 10000)
        
        try:
            # connectivity=4: Tốt cho nét vuông vức
            # mean_color=True: Lấp lỗ bằng màu lân cận
            if hasattr(img, 'connected_components'):
                img.connected_components(connectivity=4, area_threshold=area, mean_color=True)
            else:
                # Fallback cho Wand cũ
                radius = max(0.5, (area / 3.14) ** 0.5)
                img.morphology(method='open', kernel='disk', arguments=str(radius))
        except Exception as e:
             raise ValidationError(f"cca: lỗi thực thi - {e}")

    @staticmethod
    def _cmd_selective_blur(img, v):
        """
        Làm mờ chọn lọc (Smart Blur).
        Mịn da/nền giấy, xóa vân lưới (moiré) nhưng giữ nguyên nét vẽ mực.
        Cú pháp: Radius x Sigma + Threshold%. (VD: 0x2+10%).
        """
        if not v:
            raise ValidationError("selective-blur: thiếu tham số")
        
        parts = re.split(r'[x+:,]', v)
        parts = [p for p in parts if p]
        
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 1.0
        if len(parts) > 1:
             s = Validator.validate_float(parts[1], "sigma", 0, 100)
             
        t_percent = 0.1 # 10%
        if len(parts) > 2:
             t_percent = Validator.validate_percentage(parts[2], "threshold")
             
        threshold_value = t_percent * img.quantum_range
        img.selective_blur(radius=r, sigma=s, threshold=threshold_value)

    @staticmethod
    def _cmd_lat(img, v):
        """
        Phân ngưỡng thích ứng cục bộ (Local Adaptive Threshold).
        Chuyển sang đen trắng dựa trên độ sáng vùng lân cận (Tốt cho text mờ).
        Cú pháp: WxH+Offset. (VD: 20x20+10).
        """
        if not v: 
            raise ValidationError("lat: thiếu tham số (WxH+Offset)")
            
        parts = re.split(r'[x+:,]', v)
        parts = [p for p in parts if p]
        
        w = Validator.validate_positive_int(parts[0], "lat width")
        h = w if len(parts) < 2 else Validator.validate_positive_int(parts[1], "lat height")
        
        offset = 0
        if len(parts) >= 3:
            try: offset = float(parts[2])
            except: offset = 0
            
        img.adaptive_threshold(width=w, height=h, offset=offset)