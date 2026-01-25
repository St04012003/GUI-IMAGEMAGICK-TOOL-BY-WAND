# main.py
import sys
from qtpy.QtWidgets import QApplication, QMessageBox

def main():
    # Khởi tạo App trước để có thể dùng QMessageBox nếu lỗi xảy ra ngay khi import
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Giao diện hiện đại

    # ============================================================
    # 1. SETUP MÔI TRƯỜNG & KIỂM TRA DEPENDENCIES
    # ============================================================
    try:
        # Gọi hàm setup từ utils (để set biến môi trường MAGICK_HOME trước tiên)
        # Giả định file utils.py nằm cùng thư mục với main.py
        from utils import auto_setup_dependencies
        auto_setup_dependencies()
        
        # Thử import Wand để kiểm tra xem ImageMagick DLL có load được không
        # Nếu chưa setup đúng path, dòng này sẽ văng lỗi ImportError/DelegateError
        from wand.version import MAGICK_VERSION
        # print(f"DEBUG: Loaded ImageMagick: {MAGICK_VERSION}")

    except (ImportError, Exception) as e:
        # Nếu lỗi, hiện thông báo GUI thân thiện rồi thoát
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Lỗi Môi Trường")
        msg.setText("Không thể khởi động ImageMagick Tool!")
        msg.setInformativeText(
            "Tool không tìm thấy thư viện xử lý ảnh (ImageMagick/Wand).\n\n"
            f"Chi tiết lỗi: {str(e)}\n\n"
            "Cách khắc phục:\n"
            "1. Tải 'ImageMagick Portable' và giải nén cạnh file tool.\n"
            "2. Đảm bảo đã chạy lệnh 'pip install Wand'."
        )
        msg.exec()
        return # Dừng chương trình

    # ============================================================
    # 2. KHỞI ĐỘNG GIAO DIỆN (UI)
    # ============================================================
    try:
        # [CẬP NHẬT QUAN TRỌNG] 
        # Import từ package 'ui' mới thay vì file 'window' đơn lẻ cũ
        # Nhờ file ui/__init__.py, ta có thể import trực tiếp class ImageMagickTool
        from ui import ImageMagickTool
        
        window = ImageMagickTool()
        window.show()
        
        sys.exit(app.exec())

    except ImportError as e:
        # Bắt lỗi nếu bạn quên tạo file __init__.py hoặc cấu trúc folder sai
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Lỗi Cấu Trúc")
        msg.setText("Không tìm thấy module giao diện (UI).")
        msg.setInformativeText(
            f"Lỗi: {str(e)}\n\n"
            "Vui lòng kiểm tra lại xem folder 'ui' có chứa file '__init__.py' "
            "và 'main_window.py' chưa."
        )
        msg.exec()

if __name__ == "__main__":
    main()