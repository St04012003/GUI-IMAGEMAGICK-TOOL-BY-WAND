import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple

# ==============
# CONFIGURATION
# ==============
@dataclass
class Config:
    """
    Class chứa toàn bộ cấu hình của ứng dụng.
    """
    # Kích thước tối đa cho ảnh preview
    preview_max_width: int = 800
    preview_max_height: int = 1200

    # [FIX] Dùng tên file v6 để khớp với dữ liệu cũ
    preset_file: Path = Path("presets.json")
    settings_file: Path = Path("settings.ini")

    # Độ trễ (ms) trước khi chạy lệnh preview (Debounce)
    debounce_delay: int = 500
    
    # Số lượng ảnh tối đa lưu trong RAM (LRU Cache)
    cache_size: int = 600
    
    # Garbage Collection interval
    gc_interval: int = 20
    
    # Các định dạng ảnh hỗ trợ
    image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp')
    
    # Danh sách lệnh (sẽ được core.py tự động điền)
    commands: List[str] = field(default_factory=list)
    
CONFIG = Config()