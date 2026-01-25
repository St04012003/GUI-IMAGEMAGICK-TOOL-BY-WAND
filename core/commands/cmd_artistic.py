# core/cmd_artistic.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# =============================================
# 5. ARTISTIC & EFFECTS (Hiệu ứng nghệ thuật)
# =============================================
class ArtisticCommands(BaseCommand):
    @staticmethod
    def _cmd_sepia(img, v):
        """
        Hiệu ứng màu phim cũ (Sepia).
        Tham số: Ngưỡng (Threshold), mặc định 0.8.
        """
        threshold = 0.8
        if v:
            threshold = Validator.validate_percentage(v, "sepia threshold")
        img.sepia_tone(threshold=threshold)

    @staticmethod
    def _cmd_solarize(img, v):
        """
        Hiệu ứng phơi sáng quá mức (Solarize).
        Tham số: Ngưỡng (Threshold). Đảo ngược màu trên ngưỡng này.
        """
        threshold = 0.5
        if v:
            threshold = Validator.validate_percentage(v, "solarize threshold")
        img.solarize(threshold=threshold)

    @staticmethod
    def _cmd_posterize(img, v):
        """
        Giảm số lượng cấp độ màu (Posterize).
        Tham số: Số levels (VD: 4, 8, 16). Tạo hiệu ứng tranh poster.
        """
        if not v:
            raise ValidationError("posterize: thiếu số levels")
        
        levels = Validator.validate_positive_int(v, "posterize levels")
        if levels > 256:
            raise ValidationError("posterize: levels phải <= 256")
        img.posterize(levels=levels)

    @staticmethod
    def _cmd_oil_paint(img, v):
        """
        Hiệu ứng tranh sơn dầu (Oil Paint).
        Tham số: Radius (Bán kính cọ). VD: 3.
        """
        radius = 3
        if v:
            radius = Validator.validate_float(v, "oil paint radius", 0, 50)
        img.oil_paint(radius=radius)

    @staticmethod
    def _cmd_charcoal(img, v):
        """
        Hiệu ứng vẽ than chì (Charcoal).
        Cú pháp: Radius x Sigma. (VD: 0x1).
        """
        if not v:
            raise ValidationError("charcoal: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        
        img.charcoal(radius=r, sigma=s)

    @staticmethod
    def _cmd_sketch(img, v):
        """
        Hiệu ứng vẽ phác thảo (Sketch).
        Cú pháp: Radius x Sigma + Angle. (VD: 0x20+120).
        """
        if not v:
            raise ValidationError("sketch: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        a = 0 if len(parts) < 3 else Validator.validate_float(parts[2], "angle", 0, 360)
        
        img.sketch(radius=r, sigma=s, angle=a)

    @staticmethod
    def _cmd_swirl(img, v):
        """
        Hiệu ứng xoáy nước (Swirl).
        Tham số: Góc xoáy (độ). VD: 90 (xoáy phải), -90 (xoáy trái).
        """
        if not v:
            raise ValidationError("swirl: thiếu góc xoáy")
        
        degree = Validator.validate_float(v, "swirl degree", -360, 360)
        img.swirl(degree=degree)

    @staticmethod
    def _cmd_wave(img, v):
        """
        Tạo hiệu ứng lượn sóng (Wave).
        Cú pháp: Amplitude x Wavelength (Biên độ x Bước sóng). VD: 25x150.
        """
        if not v:
            raise ValidationError("wave: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        amplitude = Validator.validate_float(parts[0], "amplitude", 0, 1000)
        wavelength = amplitude * 2 if len(parts) < 2 else Validator.validate_float(parts[1], "wavelength", 0, 1000)
        
        img.wave(amplitude=amplitude, wave_length=wavelength)

    @staticmethod
    def _cmd_implode(img, v):
        """
        Hiệu ứng hút vào tâm (Implode).
        Tham số: Cường độ (0.0 đến 1.0). VD: 0.5.
        """
        amount = 0.5
        if v:
            amount = Validator.validate_float(v, "implode amount", 0, 1)
        img.implode(amount=amount)

    @staticmethod
    def _cmd_vignette(img, v):
        """
        Làm tối 4 góc ảnh (Vignette).
        Cú pháp: Radius x Sigma + X + Y. (VD: 0x20).
        """
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
        """
        Tạo khung ảnh Polaroid và bóng đổ.
        Tham số: Góc xoay ngẫu nhiên (Angle).
        """
        angle = 0
        if v:
            angle = Validator.validate_float(v, "polaroid angle", -360, 360)
        img.polaroid(angle=angle)

    @staticmethod
    def _cmd_shadow(img, v):
        """
        Tạo bóng đổ cho ảnh (Shadow).
        Cú pháp: Opacity x Sigma + X + Y. VD: 80x3+5+5.
        """
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
        """
        Giả lập hiệu ứng ban đêm (Blue Shift).
        Tham số: Factor (VD: 1.5). Giảm độ chói, tăng màu xanh.
        """
        factor = 1.5
        if v:
            factor = Validator.validate_float(v, "blue shift factor", 0.1, 10)
        img.blue_shift(factor=factor)
    
    @staticmethod
    def _cmd_emboss(img, v):
        """
        Hiệu ứng chạm nổi 3D (Emboss).
        Cú pháp: Radius x Sigma. (VD: 0x1 hoặc 2x1).
        """
        if not v:
            raise ValidationError("emboss: thiếu tham số (Radius x Sigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 50)
        
        img.emboss(radius=r, sigma=s)

    @staticmethod
    def _cmd_motion_blur(img, v):
        """
        Làm mờ chuyển động (Motion Blur).
        Cú pháp: Radius x Sigma + Angle. (VD: 0x10+45).
        """
        if not v:
            raise ValidationError("motion-blur: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 10.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        a = 0.0 if len(parts) < 3 else Validator.validate_float(parts[2], "angle", 0, 360)
        
        img.motion_blur(radius=r, sigma=s, angle=a)

    @staticmethod
    def _cmd_rotational_blur(img, v):
        """
        Làm mờ xoay tròn (Rotational/Radial Blur).
        Tham số: Angle (Góc xoay). VD: 10.
        """
        if not v:
            raise ValidationError("rotational-blur: thiếu góc xoay")
        
        angle = Validator.validate_float(v, "angle", 0, 360)
        img.rotational_blur(angle=angle)

    @staticmethod
    def _cmd_spread(img, v):
        """
        Tán xạ điểm ảnh, tạo hiệu ứng nhiễu/kính mờ (Spread).
        Tham số: Radius (Bán kính tán xạ). VD: 5.
        """
        if not v:
            raise ValidationError("spread: thiếu bán kính")
        
        radius = Validator.validate_float(v, "radius", 0, 100)
        img.spread(radius=radius)

    @staticmethod
    def _cmd_cycle_colormap(img, v):
        """
        Xoay vòng bảng màu (Psychedelic Effect).
        Tham số: Amount (Số bước dịch chuyển màu). VD: 10, 50.
        """
        if not v:
            raise ValidationError("cycle-colormap: thiếu tham số")
        
        amount = Validator.validate_int(v, "amount")
        img.cycle_colormap(amount)

    @staticmethod
    def _cmd_raise(img, v):
        """
        Tạo hiệu ứng nút nổi 3D (Raise).
        Cú pháp: WxH+X+Y (Kích thước viền). VD: 5x5.
        """
        if not v:
            raise ValidationError("raise: thiếu kích thước viền")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        img.raise_(width=w, height=h, x=x, y=y, raise_=True)

    @staticmethod
    def _cmd_lower(img, v):
        """
        Tạo hiệu ứng nút chìm 3D (Lower).
        Cú pháp: WxH+X+Y (Kích thước viền). VD: 5x5.
        """
        if not v:
            raise ValidationError("lower: thiếu kích thước viền")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        img.raise_(width=w, height=h, x=x, y=y, raise_=False)