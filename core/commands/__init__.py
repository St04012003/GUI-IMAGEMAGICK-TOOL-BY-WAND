# core/commands/__init__.py

# Import các class từ file con
from .cmd_geometry import GeometryCommands
from .cmd_settings import SettingsCommands
from .cmd_color import ColorCommands
from .cmd_filter import FiltersCommands
from .cmd_artistic import ArtisticCommands
from .cmd_decoration import DecorationCommands
from .cmd_edge import EdgeCommands

# Danh sách các class sẽ được dùng
Command_classes = [
    GeometryCommands,
    SettingsCommands,
    ColorCommands,
    FiltersCommands,
    ArtisticCommands,
    DecorationCommands,
    EdgeCommands,
]

# Tạo Dictionary chứa tất cả lệnh từ các class trên
ALL_COMMANDS = {}
for cls in Command_classes:
    if hasattr(cls, 'get_map'):
        ALL_COMMANDS.update(cls.get_map())

# Export ra ngoài để các file khác sử dụng
__all__ = ['ALL_COMMANDS', 'Command_classes']