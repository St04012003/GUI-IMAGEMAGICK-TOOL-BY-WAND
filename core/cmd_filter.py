# core/cmd_filters.py
import re
from .validator import Validator, ValidationError

# 4. FILTERS & ENHANCE (Lọc & Tăng cường)

class FiltersCommands:
    @staticmethod
    def _cmd_blur(img, v):
        # radius x sigma
        if not v:
            raise ValidationError("blur: thiếu tham số (radius hoặc radiusxsigma)")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "blur radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "blur sigma", 0, 100)
        
        img.blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_gaussian_blur(img, v):
        if not v:
            raise ValidationError("gaussian-blur: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = r if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.gaussian_blur(radius=r, sigma=s)

    @staticmethod
    def _cmd_sharpen(img, v):
        if not v:
            raise ValidationError("sharpen: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 100)
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        
        img.sharpen(radius=r, sigma=s)

    @staticmethod
    def _cmd_unsharp(img, v):
        # radius x sigma + amount + threshold
        if not v:
            raise ValidationError("unsharp: thiếu tham số")
        
        parts = re.split(r'[x+,]', v)
        parts = [x for x in parts if x]
        
        r = Validator.validate_float(parts[0], "radius", 0, 100) if len(parts) > 0 else 0
        s = 1.0 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 100)
        a = 1.0 if len(parts) < 3 else Validator.validate_float(parts[2], "amount", 0, 10)
        t = 0.05 if len(parts) < 4 else Validator.validate_float(parts[3], "threshold", 0, 1)
        
        img.unsharp_mask(radius=r, sigma=s, amount=a, threshold=t)

    @staticmethod
    def _cmd_despeckle(img, v): 
        img.despeckle()
    @staticmethod
    def _cmd_reduce_noise(img, v): 
        img.despeckle()
    @staticmethod
    def _cmd_enhance(img, v): 
        img.enhance() # Digital filter to improve quality
    
    @staticmethod
    def _cmd_noise(img, v):
        # Add noise: gaussian, impulse, laplacian, poisson, uniform...
        if not v:
            raise ValidationError("noise: thiếu loại noise")
        
        valid = ['gaussian', 'impulse', 'laplacian', 'poisson', 'uniform', 'random']
        noise_type = Validator.validate_enum(v, valid, "noise type")
        img.noise(noise_type, attenuate=1.0)

    @staticmethod
    def _cmd_median(img, v):
        # radius
        radius = 1
        if v:
            radius = Validator.validate_float(v, "median radius", 0, 50)
        size = int(radius * 2 + 1)
        img.statistic('median', width=size, height=size)

    @staticmethod
    def _cmd_kuwahara(img, v):
        # radius x sigma (Edge preserving smooth)
        if not v:
            raise ValidationError("kuwahara: thiếu tham số")
        
        parts = re.split(r'[x,]', v)
        r = Validator.validate_float(parts[0], "radius", 0, 50)
        s = 0.5 if len(parts) < 2 else Validator.validate_float(parts[1], "sigma", 0, 10)
        
        img.kuwahara(radius=r, sigma=s)
    
    @classmethod
    def get_map(cls):
        return {
            'blur': cls._cmd_blur,
            'gaussian-blur': cls._cmd_gaussian_blur,
            'sharpen': cls._cmd_sharpen,
            'unsharp': cls._cmd_unsharp,
            'despeckle': cls._cmd_despeckle,
            'reduce-noise': cls._cmd_reduce_noise,
            'noise': cls._cmd_noise,
            'median': cls._cmd_median,
            'enhance': cls._cmd_enhance,
            'kuwahara': cls._cmd_kuwahara,
            }