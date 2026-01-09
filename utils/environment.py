# utils/environment.py
import sys
import os
import subprocess
import importlib.util
from pathlib import Path
from typing import Optional

# ========================================================
# BOOTSTRAP & DEPENDENCIES SETUP - Đảm bảo môi trường
# ========================================================
MARKER_FILE = Path("env_setup.done")

def auto_setup_dependencies():
    """
    Hàm khởi động thông minh:
    - Lần đầu: Kiểm tra pip + Tìm ImageMagick -> Lưu cấu hình.
    - Lần sau: Bỏ qua kiểm tra pip, đọc cấu hình ImageMagick từ file -> Khởi động tức thì.
    """
    # 1. Chế độ khởi động nhanh (Fast Boot)
    if MARKER_FILE.exists():
        try:
            # Đọc đường dẫn đã lưu từ lần trước
            saved_path = MARKER_FILE.read_text(encoding='utf-8').strip()
            if saved_path and Path(saved_path).exists():
                _set_magick_env(Path(saved_path))
                # print("[+] Fast boot: Environment loaded.")
                return
        except Exception:
            # Nếu file lỗi, lờ đi và chạy full setup lại
            pass

    # 2. Chế độ cài đặt đầy đủ (Full Setup)
    print("[-] Đang thiết lập môi trường lần đầu (hoặc sau khi reset)...")
    _install_packages()
    
    # Tìm và cấu hình ImageMagick
    magick_home = _find_imagemagick()
    
    if magick_home:
        _set_magick_env(magick_home)
        # Lưu đường dẫn vào file đánh dấu để lần sau khởi động nhanh
        try:
            MARKER_FILE.write_text(str(magick_home), encoding='utf-8')
            print(f"[+] Đã lưu cấu hình môi trường vào {MARKER_FILE.name}")
        except Exception as e:
            print(f"[!] Không thể lưu file cấu hình: {e}")
    else:
        print("⚠️ Cảnh báo: Không tìm thấy ImageMagick Portable. Sẽ thử dùng bản hệ thống.")

    # Kiểm tra kết nối cuối cùng
    _check_wand_binding()

def _set_magick_env(magick_path: Path):
    """Thiết lập biến môi trường trỏ tới ImageMagick"""
    magick_str = str(magick_path)
    os.environ["MAGICK_HOME"] = magick_str
    os.environ["PATH"] = magick_str + os.pathsep + os.environ["PATH"]

def _install_packages():
    """Kiểm tra và cài đặt thư viện pip (Chậm - chỉ chạy khi cần)"""
    REQUIRED_PACKAGES = [("PyQt5", "PyQt5"), ("Wand", "wand")]
    
    def install(package):
        print(f"[-] Thư viện '{package}' chưa có. Đang tự động tải...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[+] Đã cài xong '{package}'.")
        except subprocess.CalledProcessError:
            print(f"[!] Lỗi: Không thể cài '{package}'. Hãy chạy Admin hoặc cài thủ công.")

    for package, import_name in REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is None:
            install(package)
            importlib.invalidate_caches()

def _find_imagemagick() -> Optional[Path]:
    """
    Logic tìm kiếm ImageMagick Portable (CẢI TIẾN: QUÉT SÂU + QUÉT NGƯỢC)
    Chiến thuật:
    1. Quét sâu (Deep Scan) từ vị trí file hiện tại xuống dưới.
    2. Nếu không thấy, leo ngược lên các thư mục cha (tối đa 3 cấp) và quét các thư mục con của chúng.
    """
    
    # 1. Xác định vị trí bắt đầu
    if getattr(sys, 'frozen', False):
        start_dir = Path(sys.executable).parent
    else:
        start_dir = Path(__file__).parent.absolute()

    print(f"[-] Bắt đầu tìm ImageMagick từ: {start_dir}")

    # Hàm phụ: Kiểm tra xem một folder có phải là ImageMagick hợp lệ không
    def _is_valid_magick_folder(folder: Path) -> bool:
        try:
            # Phải có magick.exe
            if not (folder / "magick.exe").exists():
                return False
            # Phải có ít nhất 1 file DLL CORE_RL (Dấu hiệu bản Portable)
            # Dùng glob thay vì list toàn bộ để nhanh hơn, lấy cái đầu tiên tìm được
            return any(folder.glob("CORE_RL_*.dll"))
        except PermissionError:
            return False

    # --- GIAI ĐOẠN 1: QUÉT XUỐNG (DEEP SCAN) ---
    # Tìm trong thư mục hiện tại và tất cả thư mục con
    print("[-] Phase 1: Quét sâu bên dưới (Deep Scan)...")
    
    # Kiểm tra ngay thư mục hiện tại
    if _is_valid_magick_folder(start_dir):
        return start_dir

    # Ưu tiên tìm các tên phổ biến trước cho nhanh (O(1))
    common_names = ["ImageMagick Portable", "ImageMagick", "magick", "bin"]
    for name in common_names:
        candidate = start_dir / name
        if candidate.is_dir() and _is_valid_magick_folder(candidate):
            return candidate

    # Nếu không thấy, dùng rglob (chậm hơn nhưng tìm kỹ)
    try:
        for exe_path in start_dir.rglob("magick.exe"):
            folder = exe_path.parent
            if _is_valid_magick_folder(folder):
                print(f"[+] Tìm thấy (Deep Scan): {folder.name}")
                return folder
    except Exception as e:
        print(f"[!] Lỗi khi quét xuống: {e}")

    # --- GIAI ĐOẠN 2: QUÉT NGƯỢC LÊN (UPWARD SCAN) ---
    # Leo lên thư mục cha để tìm các thư mục "anh em" (siblings)
    # Ví dụ: Code ở /Project/src, Tool ở /Project/ImageMagick
    print("[-] Phase 2: Quét ngược lên trên (Upward Scan)...")
    
    current_scan = start_dir
    max_levels_up = 3  # Chỉ leo lên tối đa 3 cấp để tránh quét cả ổ đĩa
    
    for i in range(max_levels_up):
        parent = current_scan.parent
        
        # Nếu đã chạm gốc ổ đĩa thì dừng
        if parent == current_scan: 
            break
            
        # print(f"    ... Đang kiểm tra cấp cha {i+1}: {parent}")
        
        # Tại thư mục cha, kiểm tra tất cả các thư mục con trực tiếp (siblings)
        try:
            for item in parent.iterdir():
                if item.is_dir():
                    # Nếu tên folder khớp các tên phổ biến -> Kiểm tra kỹ
                    # Hoặc kiểm tra mọi folder (nếu muốn chắc chắn 100% nhưng chậm hơn chút)
                    # Ở đây mình chọn kiểm tra mọi folder con có chứa magick.exe
                    if (item / "magick.exe").exists():
                        if _is_valid_magick_folder(item):
                            print(f"[+] Tìm thấy (Upward Scan) tại: {item}")
                            return item
        except PermissionError:
            pass # Bỏ qua các thư mục không có quyền truy cập
            
        current_scan = parent

    return None

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
