# core/cache.py
from collections import OrderedDict
from typing import Optional
from PyQt5.QtGui import QImage

# ==========================
# CLASS QUẢN LÝ CACHE (LRU)
# ==========================
class ImageCache:    
    # Quản lý bộ nhớ đệm (Cache) theo cơ chế LRU (Least Recently Used)
    def __init__(self, max_size=30):
        self.max_size = max_size # max_size: Số lượng trạng thái lệnh tối đa muốn lưu (VD: 30 lệnh)
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[QImage]:
        # Lấy ảnh từ cache. Nếu có, đưa nó lên đầu danh sách (đánh dấu vừa dùng).
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, image: QImage):
        # Lưu ảnh vào cache. Nếu đầy, xóa cái cũ nhất.
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = image
        
        # Nếu vượt quá giới hạn, xóa item đầu tiên (là cái ít dùng nhất - LRU)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
            
    def clear(self):
        # Xóa sạch cache (Dùng khi nạp ảnh gốc mới)
        self.cache.clear()