# dialog/ui.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QTextBrowser

# Import nội dung từ các file cùng thư mục (dùng dấu chấm .)
from .guide import GUIDE_CONTENT
from .reference import REFERENCE_CONTENT

class HelpDialog(QDialog):
    """Dialog hướng dẫn sử dụng và tra cứu lệnh"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hướng dẫn & Tra cứu lệnh ImageMagick")
        self.resize(1100, 800)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff; 
                color: #333333; 
                }
            
            QTabWidget::pane { 
                border: 1px solid #cccccc; 
                }
                           
            QTabBar::tab { 
                background: #e0e0e0; 
                color: #333; 
                font-size: 20px; 
                font-weight: bold;
                padding: 20px 30px; 
                min-width: 250px;                
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                }
            
            QTabBar::tab:selected { 
                background: #ffffff; 
                color: #000; 
                border-bottom: 3px solid #2196F3; 
                font-weight: bold; 
                }
            
            QPushButton { 
                background-color: #f0f0f0;
                border: 1px solid #ccc; 
                padding: 10px 12px; 
                border-radius: 4px; 
                font-size: 20px;
                }
            
            QPushButton:hover {
                background-color: #e0e0e0; 
                border-color: #bbb; 
                }
            
            QTextBrowser { 
                border: none; 
                padding: 10px; 
            }
        """)

        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_guide_tab(), "📖 Hướng dẫn nhanh")
        self.tabs.addTab(self._create_reference_tab(), "🔍 Tra cứu lệnh (Full)")
        
        layout.addWidget(self.tabs)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _create_guide_tab(self):
        """Tab hướng dẫn cơ bản"""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(GUIDE_CONTENT)
        return browser

    def _create_reference_tab(self):
        """Tab tra cứu lệnh"""
        browser = QTextBrowser()
        browser.setHtml(REFERENCE_CONTENT)
        return browser