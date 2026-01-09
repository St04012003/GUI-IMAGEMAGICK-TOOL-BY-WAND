# dialog/guide.py
from .styles import BASE_STYLE

GUIDE_CONTENT = BASE_STYLE + """
<h1>ImageMagick GUI Tool</h1>

<h2>🚀 Quy trình xử lý ảnh</h2>
<ol>
    <li><b>Bước 1:</b> Chọn <span class="key">Input</span> (File lẻ hoặc Folder chứa truyện).</li>
    <li><b>Bước 2:</b> Chọn <span class="key">Output Folder</span> (Nơi lưu kết quả).</li>
    <li><b>Bước 3:</b> Nhập lệnh vào ô Command (Gõ dấu <code>-</code> để xem gợi ý thông minh).</li>
    <li><b>Bước 4:</b> Sử dụng chế độ <span class="key">Split View</span> để so sánh ảnh gốc và ảnh sau xử lý.</li>
    <li><b>Bước 5:</b> Bấm <span class="key">START BATCH</span> để chạy hàng loạt.</li>
</ol>

<h2>⚡ Các Combo lệnh thông dụng</h2>

<p><b>1. Resize và Xoay ảnh:</b></p>
<pre>-resize 800x1200 -auto-orient</pre>

<p><b>2. Xử lý ảnh Scan (Làm trắng nền, đậm chữ):</b></p>
<pre>-grayscale -despeckle -level 10%,90% -sharpen 0x1</pre>

<p><b>3. Giảm dung lượng giữ nguyên chất lượng:</b></p>
<pre>-strip -quality 85 -depth 8</pre>

<p><b>4. Hiệu ứng nghệ thuật (Phim cũ):</b></p>
<pre>-sepia-tone 80% -vignette 0x20</pre>

<h2>💡 Mẹo sử dụng</h2>
<ul>
    <li><b>Split View:</b> Bật chế độ này để so sánh trực quan Before/After. Bạn có thể zoom/pan đồng bộ cả 2 bên.</li>
    <li><b>Presets:</b> Chuột phải vào preset để đổi tên. Dùng nút Import/Export để chia sẻ công thức.</li>
    <li><b>Natural Sort:</b> Tool tự động sắp xếp file thông minh (Chapter 1 -> Chapter 2... -> Chapter 10).</li>
</ul>
"""