# core/cmd_geometry.py
import re
from ..validator import Validator, ValidationError
from .base_command import BaseCommand

# ============================================
# 1. GEOMETRY & TRANSFORM (Biến đổi hình học)
# ============================================
class GeometryCommands(BaseCommand): 
    @staticmethod
    def _cmd_resize(img, v):
        """
        Thay đổi kích thước ảnh (Resize).
        Cú pháp: WxH (800x600), % (50%), Wx (800x), xH (x600).
        """
        if not v:
            raise ValidationError("resize: thiếu tham số (VD: 50%, 800x600)")
        
        try:
            if '%' in v:
                percent = Validator.validate_percentage(v, "resize percentage")
                if percent <= 0:
                    raise ValidationError("resize: phần trăm phải > 0")
                new_w = int(img.width * percent)
                new_h = int(img.height * percent)
                if new_w < 1 or new_h < 1:
                    raise ValidationError("resize: kích thước kết quả quá nhỏ")
                img.resize(new_w, new_h)
            else:
                w, h, _, _ = Validator.validate_geometry(v, require_positive=True)
                if w > 0 and h == 0:
                    h = int(w * img.height / img.width) if img.width > 0 else img.height
                if h > 0 and w == 0:
                    w = int(h * img.width / img.height) if img.height > 0 else img.width
                
                if w < 1 or h < 1:
                    raise ValidationError("resize: kích thước phải >= 1 pixel")
                img.resize(w, h)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"resize: lỗi không xác định - {e}")

    @staticmethod
    def _cmd_scale(img, v):
        """
        Thay đổi kích thước nhanh (Scale).
        Giống Resize nhưng thuật toán đơn giản hơn, nhanh hơn, ít khử răng cưa hơn.
        """
        if not v:
            raise ValidationError("scale: thiếu tham số")
        
        if '%' in v:
            percent = Validator.validate_percentage(v, "scale percentage")
            if percent <= 0:
                raise ValidationError("scale: phần trăm phải > 0")
            img.scale(int(img.width * percent), int(img.height * percent))
        else:
            w, h, _, _ = Validator.validate_geometry(v)
            if w < 1 or h < 1:
                raise ValidationError("scale: kích thước phải >= 1 pixel")
            img.scale(w, h)

    @staticmethod
    def _cmd_sample(img, v):
        """
        Thay đổi kích thước kiểu Pixel Art (Nearest Neighbor).
        Không làm mờ pixel, thích hợp phóng to ảnh pixel art hoặc mã vạch.
        """
        if not v:
            raise ValidationError("sample: thiếu tham số")
        
        if '%' in v:
            percent = Validator.validate_percentage(v, "sample percentage")
            if percent <= 0:
                raise ValidationError("sample: phần trăm phải > 0")
            img.sample(int(img.width * percent), int(img.height * percent))
        else:
            w, h, _, _ = Validator.validate_geometry(v)
            if w < 1 or h < 1:
                raise ValidationError("sample: kích thước phải >= 1 pixel")
            img.sample(w, h)

    @staticmethod
    def _cmd_liquid_rescale(img, v):
        """
        Co giãn thông minh bảo toàn nội dung (Liquid Rescale / Seam Carving).
        Thay đổi tỷ lệ ảnh mà không làm méo chủ thể chính.
        """
        if not v:
            raise ValidationError("liquid-rescale: thiếu tham số geometry")
        
        w, h, _, _ = Validator.validate_geometry(v)
        if w < 1 or h < 1:
            raise ValidationError("liquid-rescale: kích thước phải >= 1 pixel")
        img.liquid_rescale(w, h)

    @staticmethod
    def _cmd_extent(img, v):
        """
        Thay đổi kích thước Canvas (Thêm nền hoặc Cắt bớt).
        Cú pháp: WxH+X+Y. Màu nền lấy từ lệnh -background.
        """
        if not v:
            raise ValidationError("extent: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        final_w = w if w > 0 else img.width
        final_h = h if h > 0 else img.height
        
        if final_w < 1 or final_h < 1:
            raise ValidationError("extent: kích thước phải >= 1 pixel")
        
        img.extent(width=final_w, height=final_h, x=x, y=y)

    @staticmethod
    def _cmd_repage(img, v):
        """
        Đặt lại tọa độ trang ảo (Virtual Canvas).
        Thường dùng sau khi crop hoặc trim để loại bỏ offset tọa độ cũ.
        """
        if not v:
            img.page = (0, 0, 0, 0)
        else:
            geo = Validator.validate_geometry(v, require_positive=False)
            img.page = geo

    @staticmethod
    def _cmd_crop(img, v):
        """
        Cắt ảnh theo vùng chọn.
        Cú pháp: WxH+X+Y (VD: 500x500+10+10).
        """
        if not v:
            raise ValidationError("crop: thiếu tham số geometry")
        
        w, h, x, y = Validator.validate_geometry(v, require_positive=False)
        
        if x < 0 or y < 0:
            raise ValidationError("crop: tọa độ x, y phải >= 0")
        if x >= img.width or y >= img.height:
            raise ValidationError("crop: tọa độ nằm ngoài ảnh")
        
        right = x + w if w > 0 else img.width
        bottom = y + h if h > 0 else img.height
        
        if right > img.width or bottom > img.height:
            raise ValidationError("crop: vùng crop vượt quá kích thước ảnh")
        
        img.crop(left=x, top=y, right=right, bottom=bottom)

    @staticmethod
    def _cmd_rotate(img, v):
        """
        Xoay ảnh theo góc độ.
        Giá trị: Số độ (-360 đến 360). VD: 90 (phải), -90 (trái).
        """
        if not v:
            raise ValidationError("rotate: thiếu góc xoay")
        
        degree = Validator.validate_float(v, "rotate angle", -360, 360)
        img.rotate(degree=degree)

    @staticmethod
    def _cmd_auto_orient(img, v):
        """
        Tự động xoay ảnh đúng chiều dựa trên thông tin EXIF.
        Dùng cho ảnh chụp từ điện thoại/máy ảnh bị ngược.
        """
        img.auto_orient()

    @staticmethod
    def _cmd_deskew(img, v):
        """
        Tự động căn thẳng ảnh bị nghiêng (VD: ảnh scan văn bản).
        Tham số: Ngưỡng (Threshold), mặc định 0.4.
        """
        threshold = 0.4
        if v:
            threshold = Validator.validate_float(v, "deskew threshold", 0, 1)
        img.deskew(threshold=threshold)

    @staticmethod
    def _cmd_shear(img, v):
        """
        Làm nghiêng ảnh thành hình bình hành (Shear).
        Cú pháp: XxY hoặc A (độ). VD: 20x10.
        """
        if not v:
            raise ValidationError("shear: thiếu tham số (VD: 30 hoặc 30x45)")
        
        if 'x' in v.lower():
            parts = v.lower().split('x')
            if len(parts) != 2:
                raise ValidationError("shear: format phải là XxY (VD: 30x45)")
            x = Validator.validate_float(parts[0], "shear X", -89, 89)
            y = Validator.validate_float(parts[1], "shear Y", -89, 89)
        else:
            x = y = Validator.validate_float(v, "shear angle", -89, 89)
        
        img.shear(background=img.background_color, x=x, y=y)

    @staticmethod
    def _cmd_flip(img, v): 
        """Lật ảnh theo chiều dọc (Vertical Flip)."""
        img.flip()

    @staticmethod
    def _cmd_flop(img, v): 
        """Lật ảnh theo chiều ngang (Horizontal Flip)."""
        img.flop()

    @staticmethod
    def _cmd_transpose(img, v): 
        """Lật dọc rồi xoay 90 độ (Transpose)."""
        img.transpose()

    @staticmethod
    def _cmd_transverse(img, v): 
        """Lật ngang rồi xoay 270 độ (Transverse)."""
        img.transverse()

    @staticmethod
    def _cmd_trim(img, v): 
        """
        Tự động cắt bỏ viền màu đồng nhất xung quanh ảnh.
        Hữu ích để loại bỏ khoảng trắng thừa.
        """
        img.trim(fuzz=0)

    @staticmethod
    def _cmd_roll(img, v):
        """
        Cuộn ảnh theo trục X/Y (Roll).
        Cú pháp: +X+Y. (VD: +10+0, +0+10).
        Các pixel bị đẩy ra khỏi cạnh này sẽ xuất hiện ở cạnh đối diện.
        """
        if not v:
            raise ValidationError("roll: thiếu tham số (VD: +10+0)")
        
        # validate_geometry trả về (w, h, x, y), ta chỉ cần x, y
        _, _, x, y = Validator.validate_geometry(v, require_positive=False)
        img.roll(x=x, y=y)

    @staticmethod
    def _cmd_distort(img, v):
        """
        Biến dạng ảnh nâng cao (Distort).
        Cú pháp: Method:Args. (VD: Arc:360 hoặc Perspective:0,0,0,0...).
        Các method: affine, perspective, arc, polar, depolar, barrel...
        """
        if not v:
            raise ValidationError("distort: thiếu tham số (Method:Args)")
        
        parts = v.split(':')
        method = Validator.validate_not_empty(parts[0], "distort method").lower()
        args_str = parts[1] if len(parts) > 1 else ""
        
        # Parse args (tách bằng dấu phẩy hoặc khoảng trắng)
        if args_str:
            try:
                args = [float(x) for x in re.split(r'[,\s]+', args_str.strip()) if x]
            except ValueError:
                raise ValidationError("distort: tham số args phải là số")
        else:
            args = []
            
        try:
            img.distort(method, args)
        except Exception as e:
             raise ValidationError(f"distort: lỗi thực thi '{method}' - {e}")

    @staticmethod
    def _cmd_resample(img, v):
        """
        Thay đổi độ phân giải và kích thước ảnh tương ứng (Resample).
        Cú pháp: XxY (DPI). VD: 72x72, 300.
        Khác với -density (chỉ đổi metadata), lệnh này sẽ resize ảnh theo DPI mới.
        """
        if not v:
            raise ValidationError("resample: thiếu tham số DPI")
            
        parts = re.split(r'[x,]', v)
        x = Validator.validate_float(parts[0], "resolution X", 1, 10000)
        y = x if len(parts) == 1 else Validator.validate_float(parts[1], "resolution Y", 1, 10000)
        
        img.resample(x_res=x, y_res=y)