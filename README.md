# ImageMagick GUI Tool v6.0

**ImageMagick GUI Tool** là một ứng dụng giao diện đồ họa (GUI) mạnh mẽ được viết bằng **Python (PyQt5)**, giúp bạn xử lý ảnh hàng loạt sử dụng sức mạnh của thư viện **ImageMagick (Wand)**.

Công cụ này được thiết kế để kết hợp sự linh hoạt của dòng lệnh (CLI) với tính trực quan của giao diện đồ họa, cho phép xem trước (preview) kết quả theo thời gian thực trước khi xuất file hàng loạt.

---

## ✨ Tính Năng Nổi Bật

* **🚀 Xử lý hàng loạt (Batch Processing):** Xử lý hàng nghìn ảnh cùng lúc với đa luồng (Multithreading), không làm đơ giao diện.
* **👁️ Real-time Preview:** Xem trước kết quả xử lý ngay lập tức khi gõ lệnh.
* **🌗 Split View:** Chế độ so sánh "Trước/Sau" (Side-by-side) với khả năng đồng bộ Zoom/Pan.
* **🧠 Smart Command Editor:** Ô nhập lệnh thông minh với tính năng **Gợi ý lệnh (Autocomplete)** và **Tô màu cú pháp (Syntax Highlighting)**.
* **📂 Portable Ready:** Tự động phát hiện và sử dụng **ImageMagick Portable** đi kèm, không cần cài đặt phức tạp vào hệ điều hành.
* **💾 Presets System:** Lưu và tải lại các bộ lệnh hay dùng (Lưu trong `presets.json`).
* **🛠️ Auto Setup:** Tự động kiểm tra và cài đặt các thư viện Python thiếu (`PyQt5`, `Wand`) trong lần chạy đầu tiên.

---

## ⚙️ Yêu Cầu Hệ Thống

* **Hệ điều hành:** Windows 10/11 (Khuyên dùng), macOS, hoặc Linux.
* **Python:** Phiên bản 3.8 trở lên.
* **ImageMagick:**
    * **Khuyên dùng:** Bản **Portable** đặt trong thư mục dự án (Tool sẽ tự tìm).
    * Hoặc bản cài đặt hệ thống (Cần tích chọn "Install C/C++ headers" khi cài).

---

## 📦 Cài Đặt & Chạy

### Cách 1: Chạy từ Source Code (Khuyên dùng cho Dev)

1.  **Chuẩn bị mã nguồn:**
    Tải hoặc clone toàn bộ thư mục dự án về máy.

2.  **Cấu trúc thư mục khuyến nghị:**
    Đảm bảo thư mục `ImageMagick Portable` nằm cùng cấp với `main.py` (hoặc trong thư mục con).
    ```text
    Project/
    ├── ImageMagick Portable/  <-- Folder chứa magick.exe và các file DLL
    ├── main.py
    ├── core.py
    ├── ... (các file .py khác)
    └── requirements.txt (nếu có)
    ```

3.  **Chạy ứng dụng:**
    Mở terminal tại thư mục dự án và chạy:
    ```bash
    python main.py
    ```
    *Lưu ý: Trong lần chạy đầu tiên, tool sẽ tự động cài đặt các thư viện cần thiết (`PyQt5`, `Wand`).*

---

## 📖 Hướng Dẫn Sử Dụng

### 1. Giao diện chính
* **Cột Trái (Input/Files):** Chọn thư mục chứa ảnh và quản lý danh sách Presets.
* **Cột Giữa (Preview):** Hiển thị ảnh. Sử dụng chuột lăn để Zoom, kéo chuột để Pan. Nút **Split View** để bật chế độ so sánh.
* **Cột Phải (Controls):** Nhập lệnh xử lý, xem Log và nút **START** để chạy hàng loạt.

### 2. Cú pháp lệnh (Command Syntax)
Tool sử dụng cú pháp tương tự ImageMagick nhưng được đơn giản hóa. Các lệnh được ngăn cách bởi dấu cách.

**Các lệnh phổ biến:**

| Lệnh | Ví dụ | Mô tả |
| :--- | :--- | :--- |
| **Resize** | `-resize 800x600` | Đổi kích thước ảnh về 800x600 px. |
| **Resize %** | `-resize 50%` | Thu nhỏ ảnh còn 50%. |
| **Format** | `-format jpg` | Chuyển đổi định dạng output sang JPG. |
| **Crop** | `-crop 100x100+10+10` | Cắt ảnh kích thước 100x100 tại vị trí 10,10. |
| **Grayscale** | `-grayscale` | Chuyển ảnh sang đen trắng. |
| **Rotate** | `-rotate 90` | Xoay ảnh 90 độ. |
| **Blur** | `-blur 0x8` | Làm mờ ảnh. |
| **Sharpen** | `-sharpen 0x1` | Làm nét ảnh. |
| **Quality** | `-quality 80` | Thiết lập chất lượng ảnh nén (cho JPG/WebP). |

**Ví dụ lệnh kết hợp:**
```text
-resize 1920x1080 -format jpg -quality 85 -sharpen 0x1
