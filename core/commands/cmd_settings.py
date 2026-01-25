# core/cmd_settings.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# =====================================================
# 2. IMAGE SETTINGS & METADATA (Cài đặt & Dữ liệu ảnh)
# ====================================================
class SettingsCommands(BaseCommand):    
    @staticmethod    
    def _cmd_quality(img, v):
        """
        Thiết lập chất lượng nén JPEG/PNG.
        Giá trị: 0-100 (Càng cao càng nét, dung lượng càng lớn). VD: 90.
        """
        if not v:
            raise ValidationError("quality: thiếu giá trị (0-100)")
        
        quality = Validator.validate_positive_int(v, "quality", allow_zero=True)
        if quality > 100:
            raise ValidationError("quality: giá trị phải từ 0-100")
        img.compression_quality = quality

    @staticmethod
    def _cmd_density(img, v):
        """
        Thiết lập mật độ điểm ảnh (DPI - Resolution).
        Cú pháp: X hoặc XxY. VD: 300 (In ấn), 72 (Web).
        """
        if not v:
            raise ValidationError("density: thiếu giá trị DPI")
        
        parts = re.split(r'[x,]', v)
        x = Validator.validate_float(parts[0], "density X", 1, 10000)
        y = x if len(parts) == 1 else Validator.validate_float(parts[1], "density Y", 1, 10000)
        img.resolution = (x, y)

    @staticmethod
    def _cmd_units(img, v):
        """
        Thiết lập đơn vị đo mật độ ảnh.
        Giá trị: PixelsPerInch (PPI) hoặc PixelsPerCentimeter.
        """
        if not v:
            raise ValidationError("units: thiếu giá trị")
        
        valid = ['undefined', 'pixelsperinch', 'pixelspercentimeter']
        units = Validator.validate_enum(v, valid, "units")
        img.units = units

    @staticmethod
    def _cmd_depth(img, v):
        """
        Thiết lập độ sâu bit màu (Bit Depth).
        Giá trị: 8 (Phổ biến), 16 (Chất lượng cao), 32.
        """
        if not v:
            raise ValidationError("depth: thiếu giá trị")
        
        depth = Validator.validate_int(v, "depth")
        if depth not in [1, 4, 8, 16, 32]:
            raise ValidationError("depth: giá trị phải là 8, 16 hoặc 32")
        img.depth = depth

    @staticmethod
    def _cmd_strip(img, v):
        """
        Xóa toàn bộ Metadata/EXIF giúp giảm dung lượng file.
        Lệnh này không cần tham số.
        """
        img.strip()

    @staticmethod
    def _cmd_compress(img, v):
        """
        Thiết lập thuật toán nén ảnh.
        Giá trị: JPEG, LZW, ZIP, None, Lossless...
        """
        if not v:
            raise ValidationError("compress: thiếu loại nén")
        
        valid = ['undefined', 'no', 'bzip', 'dxt1', 'dxt3', 'dxt5', 
                 'fax', 'group4', 'jpeg', 'jpeg2000', 'lossless', 
                 'lzw', 'rle', 'zip', 'zstd', 'webp']
        
        comp = Validator.validate_enum(v, valid, "compression")
        img.compression = comp

    @staticmethod
    def _cmd_virtual_pixel(img, v):
        """
        Thiết lập cách xử lý pixel ở biên ảnh (Dùng cho Blur, Distort).
        Giá trị: transparent, white, black, mirror, tile...
        """
        if not v:
            raise ValidationError("virtual-pixel: thiếu giá trị")
            
        valid = ['undefined', 'background', 'black', 'checker-tile', 'dither', 
                 'edge', 'gray', 'horizontal-tile', 'horizontal-tile-edge', 
                 'mirror', 'random', 'tile', 'transparent', 'vertical-tile', 
                 'vertical-tile-edge', 'white']
                 
        method = Validator.validate_enum(v, valid, "virtual-pixel")
        img.virtual_pixel = method

    @staticmethod
    def _cmd_format(img, v):
        """
        Chuyển đổi định dạng ảnh đầu ra.
        Giá trị: jpg, png, webp, pdf, tiff, ico...
        """
        if not v:
            raise ValidationError("format: Thiếu định dạng (VD: jpg, png, webp)")
        
        valid_formats = [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
            'webp', 'ico', 'psd', 'svg', 'pdf',
            'dng', 'cr2', 'nef', 'arw', 'orf',
            'heic', 'avif', 'jp2', 'jxl', 'pcx', 'tga', 'exr', 'hdr'
        ]
        
        fmt = v.lower().strip()
        if fmt not in valid_formats:
            raise ValidationError(f"format: Định dạng '{v}' không phổ biến hoặc không hỗ trợ")

        alias_map = {'jpg': 'jpeg', 'tif': 'tiff'}
        final_fmt = alias_map.get(fmt, fmt)
        
        try:
            img.format = final_fmt
        except Exception as e:
            raise ValidationError(f"format: Không thể chuyển sang định dạng '{fmt}': {e}")
    
    @staticmethod
    def _cmd_interlace(img, v):
        """
        Chế độ hiển thị dần (Interlace/Progressive).
        Giá trị: None, Line, Plane, Partition. (Thường dùng Plane cho Web).
        Giúp ảnh hiện ra từ mờ đến rõ thay vì tải từng dòng.
        """
        if not v:
            img.interlace_scheme = 'plane' # Mặc định tốt nhất cho Web
        else:
            valid = ['none', 'line', 'plane', 'partition', 'gif', 'jpeg', 'png']
            img.interlace_scheme = Validator.validate_enum(v, valid, "interlace")

    @staticmethod
    def _cmd_sampling_factor(img, v):
        """
        Hệ số lấy mẫu màu (Chroma Subsampling).
        Cú pháp: Y:Cb:Cr. (VD: 4:2:0, 4:4:4, 2x2).
        - 4:2:0 : Giảm dung lượng 50%, mắt thường khó nhận ra (Chuẩn Web).
        - 4:4:4 : Giữ nguyên chất lượng màu (Dùng cho in ấn).
        """
        if not v:
            raise ValidationError("sampling-factor: thiếu tham số (VD: 4:2:0)")
        
        # Wand sử dụng option 'sampling-factor' thông qua options dict
        img.options['jpeg:sampling-factor'] = v

    @staticmethod
    def _cmd_loop(img, v):
        """
        Số lần lặp lại ảnh động (GIF Loop).
        Giá trị: 0 (Lặp vô hạn), hoặc số lần cụ thể (1, 2...).
        """
        if not v:
            img.loop = 0 # Mặc định vô hạn
        else:
            img.loop = Validator.validate_positive_int(v, "loop iterations", allow_zero=True)

    @staticmethod
    def _cmd_delay(img, v):
        """
        Thời gian trễ giữa các khung hình GIF (Delay).
        Đơn vị: ticks (thường là 1/100 giây). VD: 10 = 0.1s, 100 = 1s.
        """
        if not v:
            raise ValidationError("delay: thiếu thời gian (ticks)")
            
        ticks = Validator.validate_positive_int(v, "delay ticks")
        
        # Nếu là ảnh động, set delay cho tất cả các frame
        if img.animation:
            for frame in img.sequence:
                frame.delay = ticks
        else:
            img.delay = ticks

    @staticmethod
    def _cmd_fuzz(img, v):
        """
        Độ sai số màu (Fuzz distance).
        Cú pháp: Giá trị hoặc %. (VD: 10%, 2000).
        Dùng cho lệnh -trim, -transparent để chọn màu không cần chính xác tuyệt đối.
        """
        if not v:
            # Reset về mặc định
            if 'fuzz' in img.options:
                del img.options['fuzz']
        else:
            # Validate cơ bản (cho phép % hoặc số)
            if '%' in v:
                Validator.validate_percentage(v, "fuzz")
            else:
                try:
                    float(v)
                except ValueError:
                    raise ValidationError("fuzz: giá trị không hợp lệ")
            
            # Wand quản lý fuzz qua thuộc tính artifact hoặc options tùy phiên bản
            # Cách an toàn nhất là set qua options để các lệnh sau (trim) tự dùng
            img.options['fuzz'] = v