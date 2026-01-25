from qtpy.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QProgressBar, QTextEdit)
from qtpy.QtCore import Qt, Signal

from widgets import SmartCommandEdit, create_button, create_groupbox

# =============
# RIGHT PANEL
# =============
class RightPanel(QWidget):
    req_start_batch = Signal()
    req_stop_batch = Signal()
    req_help = Signal()
    command_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._create_batch_group())
        splitter.addWidget(self._create_log_group())
        splitter.addWidget(self._create_command_group())
        splitter.setSizes([120, 200, 200])
        
        layout.addWidget(splitter)
        layout.addLayout(self._create_footer())

    def _create_batch_group(self):
        group, layout = create_groupbox("Batch Processing")
        layout.setSpacing(2)
        layout.setContentsMargins(5,5,5,5)
        
        self.btn_start = create_button("START BATCH", self.req_start_batch.emit, "background-color: #4CAF50; color: white; font-weight: bold;", 35)
        self.btn_stop = create_button("STOP", self.req_stop_batch.emit, "background-color: #F44336; color: white; font-weight: bold;", 35)
        self.btn_stop.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(35)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.progress_bar)
        return group

    def _create_log_group(self):
        group, layout = create_groupbox("Progress Log")
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #2b2b2b; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.txt_log)
        return group

    def _create_command_group(self):
        group, layout = create_groupbox("Command Input")
        self.txt_command = SmartCommandEdit()
        self.txt_command.textChanged.connect(self.command_changed.emit)
        self.txt_command.setMinimumHeight(150)
        layout.addWidget(self.txt_command)
        return group

    def _create_footer(self):
        footer = QHBoxLayout()
        self.btn_help = create_button("Hướng dẫn", self.req_help.emit, "background-color: #008CBA; color: white; font-weight: bold;", 40)
        self.btn_clear = create_button("Clear Command", lambda: self.txt_command.clear(), "background-color: #ff5722; color: white; font-weight: bold;", 40)
        footer.addWidget(self.btn_help)
        footer.addWidget(self.btn_clear)
        return footer

    def append_log(self, msg):
        self.txt_log.append(msg)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())