# v3.0/core/cache.py
from collections import OrderedDict
from typing import Optional
from qtpy.QtGui import QImage

# ==========================
# CLASS QUẢN LÝ CACHE (MEMORY AWARE)
# ==========================
class ImageCache:    
    """
    Quản lý bộ nhớ đệm dựa trên dung lượng (Size-based LRU).
    Mục tiêu: Giới hạn RAM sử dụng (mặc định 500MB) thay vì số lượng ảnh.
    """
    def __init__(self, max_size_mb=500):
        # Không cần max_size cũ nữa vì Main Window đã cập nhật chuẩn
        self.cache = OrderedDict()
        self.max_size_bytes = max_size_mb * 1024 * 1024 # Đổi MB sang Bytes
        self.current_size = 0

    def get(self, key: str) -> Optional[QImage]:
        """Lấy ảnh và đưa lên đầu danh sách (đánh dấu vừa dùng)"""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, image: QImage):
        """Lưu ảnh và tự động xóa bớt nếu tràn bộ nhớ"""
        if not image: return

        # Tính dung lượng ảnh: Width * Height * 4 (RGBA 4 bytes/pixel)
        img_size = image.width() * image.height() * 4
        
        # Nếu key đã tồn tại (ghi đè), phải trừ dung lượng ảnh cũ đi trước
        if key in self.cache:
            old_img = self.cache[key]
            self.current_size -= (old_img.width() * old_img.height() * 4)
            self.cache.move_to_end(key)
        
        # Thêm ảnh mới vào cache
        self.cache[key] = image
        self.current_size += img_size
        
        # Kiểm tra tràn bộ nhớ (Eviction Policy)
        # Nếu dung lượng hiện tại > giới hạn -> Xóa item cũ nhất (đầu list)
        while self.current_size > self.max_size_bytes and self.cache:
            old_k, old_img = self.cache.popitem(last=False)
            
            # Trừ dung lượng của item vừa xóa
            removed_size = old_img.width() * old_img.height() * 4
            self.current_size -= removed_size

    def clear(self):
        """Reset toàn bộ cache"""
        self.cache.clear()
        self.current_size = 0