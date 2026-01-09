# core/cmd_color.py
import re
from .validator import Validator, ValidationError

# 3. COLOR & CHANNEL (Màu sắc & Kênh màu)

class ColorCommands:
    @staticmethod
    def _cmd_colorspace(img, v):
        # gray, rgb, cmyk, srgb, hsl, hsb...
        if not v:
            raise ValidationError("colorspace: thiếu giá trị")
        
        valid = ['rgb', 'srgb', 'gray', 'cmyk', 'hsl', 'hsb', 'lab', 'xyz']
        cs = Validator.validate_enum(v, valid, "colorspace")
        try:
            img.transform_colorspace(cs)
        except Exception as e:
            raise ValidationError(f"colorspace: không thể chuyển đổi - {e}")

    @staticmethod
    def _cmd_type(img, v):
        # grayscale, bilevel, truecolor, palette...
        if not v:
            raise ValidationError("type: thiếu giá trị")
        
        valid = ['bilevel', 'grayscale', 'palette', 'truecolor', 'colorseparation', 'optimize']
        img_type = Validator.validate_enum(v, valid, "type")
        img.type = img_type
        
    @staticmethod
    def _cmd_monochrome(img, v):
        # Chuyển thành ảnh đen trắng 2 màu (1-bit dithered)
        img.type = 'bilevel'

    @staticmethod
    def _cmd_alpha(img, v):
        # activate, deactivate, set, opaque, transparent...
        if not v:
            raise ValidationError("alpha: thiếu mode (on/off/remove)")
        
        valid = ['on', 'off', 'activate', 'deactivate', 'remove', 'set']
        mode = Validator.validate_enum(v, valid, "alpha")
        
        if mode in ['off', 'deactivate']:
            img.alpha_channel = False
        elif mode in ['on', 'activate']:
            img.alpha_channel = True
        elif mode == 'remove':
            img.alpha_channel = 'remove'

    @staticmethod
    def _cmd_background(img, v):
        if not v:
            raise ValidationError("background: thiếu màu")
        
        color = Validator.validate_color(v)
        img.background_color = color

    @staticmethod
    def _cmd_transparent(img, v):
        # Biến một màu thành trong suốt. VD: -transparent white
        if not v:
            raise ValidationError("transparent: thiếu màu")
        
        color = Validator.validate_color(v)
        img.transparent_color(color=color, alpha=0.0)


    @staticmethod
    def _cmd_brightness_contrast(img, v):
        # brightness x contrast (VD: 10x20)
        if not v:
            raise ValidationError("brightness-contrast: thiếu giá trị (VD: 10x20)")
        
        parts = re.split(r'[x,]', v)
        if len(parts) < 1:
            raise ValidationError("brightness-contrast: format không hợp lệ")
        
        b = Validator.validate_float(parts[0], "brightness", -100, 100)
        c = 0 if len(parts) < 2 else Validator.validate_float(parts[1], "contrast", -100, 100)
        img.brightness_contrast(brightness=b, contrast=c)

    @staticmethod
    def _cmd_level(img, v):
        # black_point, white_point, gamma
        if not v:
            raise ValidationError("level: thiếu giá trị")
        
        parts = v.replace('%', '').split(',')
        b = Validator.validate_float(parts[0], "black point", 0, 100) / 100.0
        w = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "white point", 0, 100) / 100.0
        g = 1.0 if len(parts) < 3 else Validator.validate_float(parts[2], "gamma", 0.1, 10)
        
        if b >= w:
            raise ValidationError("level: black point phải < white point")
        
        img.level(black=b, white=w, gamma=g)

    @staticmethod
    def _cmd_threshold(img, v):
        # Chuyển đen trắng dựa trên ngưỡng (VD: 50%)
        if not v:
            raise ValidationError("threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "threshold")
        img.threshold(threshold=t)
            
    @staticmethod
    def _cmd_black_threshold(img, v):
        # Buộc các màu dưới ngưỡng thành màu đen
        if not v:
            raise ValidationError("black-threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "black-threshold")
        img.black_threshold(threshold=t)

    @staticmethod
    def _cmd_white_threshold(img, v):
        # Buộc các màu trên ngưỡng thành màu trắng
        if not v:
            raise ValidationError("white-threshold: thiếu giá trị")
        
        t = Validator.validate_percentage(v, "white-threshold")
        img.white_threshold(threshold=t)

    @staticmethod
    def _cmd_gamma(img, v):
        # Gamma correction
        if not v:
            raise ValidationError("gamma: thiếu giá trị")
        
        gamma = Validator.validate_float(v, "gamma", 0.1, 10)
        img.gamma(gamma)

    @staticmethod
    def _cmd_auto_level(img, v): 
        img.auto_level()

    @staticmethod
    def _cmd_auto_gamma(img, v): 
        img.auto_gamma()

    @staticmethod
    def _cmd_normalize(img, v): 
        img.normalize()

    @staticmethod
    def _cmd_equalize(img, v): 
        img.equalize()

    @staticmethod
    def _cmd_negate(img, v): 
        img.negate()

    @staticmethod
    def _cmd_grayscale(img, v): 
        img.type = 'grayscale'

    @staticmethod
    def _cmd_modulate(img, v):
        # brightness, saturation, hue (100,100,100 is default)
        if not v:
            raise ValidationError("modulate: thiếu giá trị (brightness,saturation,hue)")
        
        parts = v.split(',')
        b = Validator.validate_float(parts[0], "brightness", 0, 200)
        s = 100 if len(parts) < 2 else Validator.validate_float(parts[1], "saturation", 0, 200)
        h = 100 if len(parts) < 3 else Validator.validate_float(parts[2], "hue", 0, 200)
        
        img.modulate(brightness=b, saturation=s, hue=h)

    @staticmethod
    def _cmd_sigmoidal_contrast(img, v):
        # contrast x midpoint (VD: 3x50%)
        if not v:
            raise ValidationError("sigmoidal-contrast: thiếu giá trị")
        
        parts = re.split(r'[x,]', v.replace('%',''))
        c = Validator.validate_float(parts[0], "contrast", 0, 20)
        m = 0.5 if len(parts) < 2 else Validator.validate_float(parts[1], "midpoint", 0, 100) / 100.0
        
        img.sigmoidal_contrast(strength=c, midpoint=m)


    @staticmethod
    def _cmd_colorize(img, v):
        # Tô màu phủ lên ảnh: color, alpha (VD: red,50)
        if not v:
            raise ValidationError("colorize: thiếu màu")
        
        parts = v.split(',')
        color = Validator.validate_color(parts[0])
        alpha = parts[1] if len(parts) > 1 else "100%"
        
        img.colorize(color=color, alpha=alpha)

    @classmethod
    def get_map(cls):
        return {
            'grayscale': cls._cmd_grayscale,
            'monochrome': cls._cmd_monochrome, # NEW
            'colorspace': cls._cmd_colorspace,
            'type': cls._cmd_type,
            'alpha': cls._cmd_alpha,
            'background': cls._cmd_background,
            'transparent': cls._cmd_transparent,
            'negate': cls._cmd_negate,
            'level': cls._cmd_level,
            'auto-level': cls._cmd_auto_level,
            'auto-gamma': cls._cmd_auto_gamma,
            'brightness-contrast': cls._cmd_brightness_contrast,
            'modulate': cls._cmd_modulate,
            'normalize': cls._cmd_normalize,
            'equalize': cls._cmd_equalize,
            'gamma': cls._cmd_gamma, # NEW
            'threshold': cls._cmd_threshold, # NEW
            'black-threshold': cls._cmd_black_threshold, # NEW
            'white-threshold': cls._cmd_white_threshold, # NEW
            'sigmoidal-contrast': cls._cmd_sigmoidal_contrast,
            'colorize': cls._cmd_colorize,
            }