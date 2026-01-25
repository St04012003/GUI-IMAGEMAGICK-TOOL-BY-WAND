# core/commands/base.py

# ==============
# BASE COMMAND
# ==============
class BaseCommand:
    """
    Class cơ sở cho các nhóm lệnh.
    Tự động quét các hàm _cmd_... và tạo map lệnh.
    """
    ALIASES = {} 

    @classmethod
    def get_map(cls):
        command_map = {}
        # ... (giữ nguyên logic tự động quét của bạn ở đây) ...
        # 1. Tự động quét
        for attr_name in dir(cls):
            if attr_name.startswith("_cmd_"):
                func = getattr(cls, attr_name)
                cmd_name = attr_name[5:].replace('_', '-')
                command_map[cmd_name] = func

        # 2. Xử lý Alias
        for alias_cmd, func_name in cls.ALIASES.items():
            if hasattr(cls, func_name):
                command_map[alias_cmd] = getattr(cls, func_name)
                
        return command_map
    