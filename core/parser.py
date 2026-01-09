# core/parser.py
import re
from typing import List, Tuple, Optional
from config import CONFIG
from utils import handle_errors

# Import các module Ops
from .cmd_geometry import GeometryCommands
from .cmd_settings import SettingsCommands
from .cmd_color import ColorCommands
from .cmd_filter import FiltersCommands     
from .cmd_artistic import ArtisticCommands
from .cmd_decoration import DecorationCommands
from .cmd_edge import EdgeCommands



class CommandParser:
    """
    Trình phân tích cú pháp lệnh trung tâm.
    """

    # Tổng hợp DISPATCH từ các module con
    DISPATCH = {}
    DISPATCH.update(GeometryCommands.get_map())
    DISPATCH.update(SettingsCommands.get_map())
    DISPATCH.update(ColorCommands.get_map())
    DISPATCH.update(FiltersCommands.get_map()) 
    DISPATCH.update(ArtisticCommands.get_map())
    DISPATCH.update(DecorationCommands.get_map())
    DISPATCH.update(EdgeCommands.get_map())
    

    @staticmethod
    def parse(command_string: str) -> List[Tuple[str, Optional[str]]]:
        # Tách chuỗi lệnh thành danh sách các cặp (lệnh, giá trị)
        # Chuẩn hóa: thêm khoảng trắng quanh dấu phẩy, xóa khoảng trắng thừa
        cleaned_cmd = re.sub(r',\s+', ',', command_string.strip())
        tokens = cleaned_cmd.split()
        
        operations = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Kiểm tra xem token có phải là lệnh (bắt đầu bằng '-', không phải số âm)
            if token.startswith('-') and len(token) > 1 and not (token[1].isdigit() or (token[1] == '.' and len(token) > 2)):
                cmd = token[1:].lower()
                value = None
                
                # Kiểm tra token tiếp theo có phải là giá trị không
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    is_next_command = (
                        next_token.startswith('-') and 
                        len(next_token) > 1 and 
                        not (next_token[1].isdigit() or (next_token[1] == '.' and len(next_token) > 2))
                    )
                    if not is_next_command:
                        value = next_token
                        i += 1
                
                operations.append((cmd, value))
            i += 1
        
        return operations
    
    @classmethod
    @handle_errors()
    def apply_commands(cls, img, operations: List[Tuple[str, Optional[str]]]):
        """Áp dụng danh sách lệnh lên đối tượng ảnh Wand"""
        for cmd, value in operations:
            handler = cls.DISPATCH.get(cmd)
            if handler:
                try:
                    handler(img, value)
                except Exception as e:
                    print(f"⚠️ Lỗi khi thực thi lệnh '-{cmd} {value}': {e}")
            else:
                print(f"⚠️ Lệnh không xác định hoặc chưa hỗ trợ: -{cmd}")
        return img
    
    @classmethod
    def _init_config_commands(cls):
        """Tự động điền danh sách lệnh vào Config để Autocomplete"""
        CONFIG.commands = sorted([f"-{cmd}" for cmd in cls.DISPATCH.keys()])

# Khởi chạy cập nhật Config ngay khi class được định nghĩa
CommandParser._init_config_commands()