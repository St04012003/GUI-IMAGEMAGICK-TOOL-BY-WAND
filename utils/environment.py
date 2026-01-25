# utils/environment.py
import sys
import os
import importlib.util
from pathlib import Path
from typing import Optional

# =================
# CONFIGURATION
# =================
MARKER_FILE = Path("env_setup.done")

# ============================================================================
# BOOTSTRAP & DEPENDENCIES SETUP - Khởi tạo môi trường trước khi App chạy
# ============================================================================
def auto_setup_dependencies():
    """
    Tự động cấu hình môi trường chạy ứng dụng.
    
    Quy trình thực hiện:
    1. Kiểm tra Dependencies -> Nếu thiếu: Dừng chương trình và yêu cầu cài từ requirements.txt.
    2. Fast Boot (Khởi động nhanh): Nếu đã có file config, load đường dẫn ngay.
    3. Slow Boot (Lần đầu): Tự động quét tìm ImageMagick Portable.
    4. Verification: Kiểm tra lại xem Wand có load được DLL không.
    """

    # BƯỚC 1. KIỂM TRA THƯ VIỆN (CRITICAL)
    _check_dependencies()

    # BƯỚC 2. CẤU HÌNH IMAGEMAGICK 
    # A. Chế độ Khởi động nhanh (Fast Boot)
    # Nếu file 'env_setup.done' tồn tại, chỉ cần đọc đường dẫn từ file này và thiết lập biến môi trường.
    if MARKER_FILE.exists():
        try:
            saved_path = MARKER_FILE.read_text(encoding='utf-8').strip()
            if saved_path and Path(saved_path).exists():
                _set_magick_env(Path(saved_path))
                return
        except Exception:
            pass

    # B. Chế độ Quét đầy đủ (Full Scan)
    # Chạy khi mở App lần đầu hoặc khi file 'env_setup.done' bị xóa.
    print("[-] Đang tìm kiếm ImageMagick Portable...")
    magick_home = _find_imagemagick()
    
    if magick_home:
        _set_magick_env(magick_home)
        try:
            MARKER_FILE.write_text(str(magick_home), encoding='utf-8')
            print(f"[+] Đã lưu cấu hình môi trường vào {MARKER_FILE.name}")
        except Exception as e:
            print(f"[!] Không thể lưu file cấu hình: {e}")
    else:
        print("⚠️ Cảnh báo: Không tìm thấy ImageMagick Portable. Sẽ thử dùng bản hệ thống.")

    # BƯỚC 3. CHECK WAND BINDING
    # Thử import Wand lần cuối để chắc chắn không bị lỗi dll
    _check_wand_binding()


# ================================
# CORE - CÁC HÀM XỬ LÝ CỐT LÕI)
# ================================
def _check_dependencies():
    """
    Kiểm tra xem các thư viện trong 'requirements.txt' đã được cài chưa.
    Nếu thiếu -> In hướng dẫn cài đặt và Exit chương trình.
    """
    # Format: (Tên module khi import, Tên package hiển thị)
    REQUIRED = [
        ("PySide6", "PySide6"),
        ("qtpy", "QtPy"),
        ("wand", "Wand")
    ]
    
    missing = []
    
    for module_name, package_name in REQUIRED:
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    
    if missing:
        print("\n" + "!"*60)
        print("🛑 LỖI: THIẾU THƯ VIỆN CẦN THIẾT (MISSING DEPENDENCIES)")
        print("!"*60)
        print(f"\nCác thư viện sau chưa được cài đặt: {', '.join(missing)}")
        print("-" * 60)
        print("Vui lòng mở Terminal/Command Prompt và chạy lệnh sau:")
        print("\n   pip install -r requirements.txt\n")
        print("-" * 60)
        print("Sau đó hãy chạy lại tool.")
        print("!"*60 + "\n")
        
        # Dừng chương trình ngay lập tức.
        # Dùng input() để giữ cửa sổ console không bị tắt ngay nếu user chạy click đúp.
        try:
            input("Nhấn Enter để thoát...")
        except:
            pass
        sys.exit(1)

def _set_magick_env(magick_path: Path):
    """Thiết lập biến môi trường trỏ tới ImageMagick"""
    magick_str = str(magick_path)
    os.environ["MAGICK_HOME"] = magick_str
    os.environ["PATH"] = magick_str + os.pathsep + os.environ["PATH"]

def _check_wand_binding():
    """Kiểm tra xem Wand có load được thư viện không"""
    try:
        from wand.version import MAGICK_VERSION
        # print(f"[+] ImageMagick OK: {MAGICK_VERSION}")
    except ImportError:
        print("\n" + "="*60)
        print("⚠️  LỖI: KHÔNG TÌM THẤY IMAGEMAGICK!")
        print("Vui lòng tải bản Portable và giải nén cạnh file tool.")
        print("="*60 + "\n")

# =================================
# DISCOVERY - TÌM KIẾM NÂNG CAO)
# =================================
def _find_imagemagick() -> Optional[Path]:
    """
    Thuật toán tìm kiếm thư mục ImageMagick Portable. Gồm:
    1. Deep Scan (Quét Xuống): Tìm trong thư mục hiện tại và các thư mục con.
    2. Upward Scan (Quét Ngược): Leo ngược lên các thư mục cha để tìm các folder "anh em".
    """
    # 1. Kiểm tra tính hợp lệ của folder
    def _is_valid_magick_folder(folder: Path) -> bool:
        try:
            # Điều kiện 1: Phải có file thực thi magick.exe
            if not (folder / "magick.exe").exists(): 
                return False
            # Điều kiện 2: Phải có các file DLL cốt lõi (dấu hiệu bản Portable)
            return any(folder.glob("CORE_RL_*.dll"))
        except PermissionError: 
            return False

    # 2. Xác định vị trí bắt đầu
    if getattr(sys, 'frozen', False):
        start_dir = Path(sys.executable).parent
    else:
        # Lên 1 cấp khỏi folder utils để quét từ root project
        start_dir = Path(__file__).parent.parent.absolute()

    print(f"[-] Bắt đầu quét từ: {start_dir}")

    # 3. Quét (Scan)
    # Phase 1: Deep Scan (Quét xuống)
    if _is_valid_magick_folder(start_dir): return start_dir
    
    common_names = ["ImageMagick Portable", "ImageMagick", "magick", "bin"]
    for name in common_names:
        candidate = start_dir / name
        if candidate.is_dir() and _is_valid_magick_folder(candidate):
            return candidate

    # Phase 2: Upward Scan (Quét ngược lên các folder cha)
    current_scan = start_dir
    for _ in range(3): # Leo tối đa 3 cấp
        parent = current_scan.parent
        if parent == current_scan: break # Đã chạm gốc ổ đĩa
        try:
            for item in parent.iterdir():
                if item.is_dir() and (item / "magick.exe").exists():
                    if _is_valid_magick_folder(item):
                        print(f"[+] Tìm thấy: {item}")
                        return item
        except: pass
        current_scan = parent

    return None