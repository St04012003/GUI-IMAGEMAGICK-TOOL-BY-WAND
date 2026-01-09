# utils/decorators.py
from functools import wraps

# ========================================================
# ERROR HANDLING
# ========================================================
def handle_errors(default_return=None, log_func=print):
    """
    Decorator dùng để bọc các hàm dễ gây lỗi (như xử lý ảnh).
    Nếu lỗi, nó sẽ in ra log thay vì làm crash chương trình.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func(f"⚠️ Error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator