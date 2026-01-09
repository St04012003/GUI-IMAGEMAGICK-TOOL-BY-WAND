# core/cmd_artistic.py
import re
from .validator import Validator, ValidationError

# 5. ARTISTIC & EFFECTS (Hiệu ứng nghệ thuật)

class ArtisticCommands:
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

    @classmethod
    def get_map(cls):
        return {
            'sepia-tone': cls._cmd_sepia,
            'sepia': cls._cmd_sepia, # Alias
            'solarize': cls._cmd_solarize,
            'posterize': cls._cmd_posterize,
            'oil-paint': cls._cmd_oil_paint,
            'charcoal': cls._cmd_charcoal,
            'sketch': cls._cmd_sketch,
            'swirl': cls._cmd_swirl,
            'wave': cls._cmd_wave,
            'implode': cls._cmd_implode,
            'vignette': cls._cmd_vignette,
            'polaroid': cls._cmd_polaroid,
            'shadow': cls._cmd_shadow,
            'blue-shift': cls._cmd_blue_shift,
            }
