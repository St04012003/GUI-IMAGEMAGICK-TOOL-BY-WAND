# main.py

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

def main():
    # Khởi tạo App trước để có thể dùng QMessageBox nếu lỗi
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Giao diện hiện đại

    # 1. Setup môi trường & Kiểm tra lỗi
    try:
        # Gọi hàm setup từ utils
        from utils import auto_setup_dependencies
        auto_setup_dependencies()
        
        # Thử import Wand để kiểm tra xem ImageMagick có hoạt động không
        # Nếu chưa cài hoặc sai đường dẫn, dòng này sẽ gây ra ImportError
        from wand.version import MAGICK_VERSION
        # print(f"Loaded ImageMagick: {MAGICK_VERSION}")

    except ImportError:
        # Nếu lỗi, hiện thông báo GUI rồi thoát
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Lỗi Môi Trường")
        msg.setText("Không tìm thấy ImageMagick!")
        msg.setInformativeText(
            "Tool không thể khởi động vì thiếu thư viện xử lý ảnh.\n\n"
            "Vui lòng tải bản 'ImageMagick Portable' và giải nén vào thư mục cạnh file tool."
        )
        msg.exec_()
        return # Dừng chương trình tại đây

    # 2. Nếu không lỗi -> Import Window và chạy
    # Import ở đây an toàn vì biến môi trường đã được set thành công
    from window import ImageMagickTool
    
    window = ImageMagickTool()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()