# dialog/styles.py
# ===================
# HELP_DIALOG_STYLES
# ===================

# ----------- 1. Style cho nội dung HTML (Hướng dẫn sử dụng) --------------
BASE_STYLE = """
<style>
    body { 
        font-family: Segoe UI, sans-serif; 
        color: #333; 
        line-height: 1.6; 
    }
    h1 { 
        color: #C2185B; 
        border-bottom: 2px solid #eee; 
        padding-bottom: 10px; 
        margin-top: 0; 
    }
    h2 { 
        color: #1976D2; 
        margin-top: 25px; 
        margin-bottom: 10px; 
    }
    li { 
        margin-bottom: 8px; 
        font-size: 18px; 
    }
    p { 
        margin-bottom: 10px; 
    }
    
    /* Khung Code */
    pre { 
        background-color: #f5f5f5; 
        color: #2E7D32; 
        padding: 12px; 
        border: 1px solid #ddd; 
        border-radius: 4px; 
        font-family: Consolas, monospace;
        font-weight: bold;
        font-size: 18px;
    }
    
    /* Highlight từ khóa */
    .key { 
        font-weight: bold; 
        color: #E65100; 
        background-color: #fff3e0; 
        padding: 2px 5px; 
        border-radius: 3px; 
    }
    code { 
        background-color: #eee; 
        padding: 2px 4px; 
        border-radius: 3px; 
        font-family: Consolas; 
        color: #333; 
    }
</style>
"""
# ------------ 2. Style cho Bảng lệnh (Reference) --------------
TABLE_STYLE = """
<style>
    body { 
        font-family: 'Segoe UI', sans-serif; 
        font-size: 14px; 
        color: #333;
        /* Padding body giúp nội dung không dính sát lề */
        padding: 15px 20px; 
        margin: 0;
    }
    
    h3 { 
        background-color: #f5f5f5; 
        color: #455a64; 
        padding: 10px; 
        border-radius: 4px; 
        border-left: 5px solid #607d8b; 
        margin-top: 25px; 
        margin-bottom: 10px;
        margin-left: 0;
        margin-right: 0; 
        font-size: 16px; 
        font-weight: bold;
        width: 100%;
    }
    
    table { 
        border-collapse: collapse; 
        margin-bottom: 15px; 
    }
    
    th { 
        text-align: left; 
        background-color: #1976D2; 
        color: white; 
        padding: 8px 10px; 
        border: 1px solid #1976D2;
        /* Width đã được set cứng trong HTML, không cần CSS ở đây nữa */
    }
    
    td { 
        border: 1px solid #ddd; 
        padding: 6px 10px; 
        color: #333; 
        vertical-align: top;
        
        /* Đảm bảo text tự xuống dòng */
        white-space: normal;
        word-wrap: break-word;
    }
    
    tr:nth-child(even) { background-color: #f9f9f9; }
    
    code { 
        font-size: 18px;
        color: #c62828; 
        font-weight: bold; 
        font-family: Consolas, monospace; 
        background-color: #ffebee;
        padding: 3px 6px; 
        border-radius: 4px; 
        display: inline-block; 
        border: 1px solid #ffcdd2;
        white-space: pre-wrap;
        word-break: break-all;
    }
    
    .ref-container { padding: 5px; }
</style>
"""

# -------------- 3. Style cho cửa sổ Dialog (QSS - Qt Style Sheet) -------------------
DIALOG_STYLES = """
    QDialog {
        background-color: #ffffff;
    }
    
    /* Vùng hiển thị nội dung text */
    QTextBrowser {
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        border-radius: 4px;
        padding: 5px;
    }
    
    /* Nút đóng */
    QPushButton {
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 13px;
        color: #333333;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
        border-color: #999999;
    }
    QPushButton:pressed {
        background-color: #d0d0d0;
        border-color: #666666;
    }
    
    /* Thanh cuộn hiện đại (Scrollbar) */
    QScrollBar:vertical {
        border: none;
        background: #f1f1f1;
        width: 10px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #c1c1c1;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a8a8a8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
"""