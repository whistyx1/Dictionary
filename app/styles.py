APP_STYLE = """
QWidget { background: #f5fbf6; color: #173d28; font-family: "Segoe UI"; font-size: 14px; }
QMainWindow { background: #edf8f0; }
QTabWidget::pane { border: 1px solid #cbe5d1; border-radius: 14px; background: white; top: -1px; }
QTabBar::tab { background: #dff1e3; color: #27633d; padding: 11px 18px; margin-right: 3px; border-radius: 8px 8px 0 0; }
QTabBar::tab:selected { background: #2f855a; color: white; }
QLabel#title { font-size: 25px; font-weight: 700; color: #22543d; }
QLabel#subtitle { color: #5d7565; }
QLabel#imageCard { background: #eef7f0; border: 2px dashed #b7d9bf; border-radius: 18px; color: #668570; }
QLineEdit, QComboBox { background: white; border: 1px solid #b8d7c0; border-radius: 9px; padding: 10px; min-height: 22px; }
QLineEdit:focus, QComboBox:focus { border: 2px solid #38a169; }
QRadioButton { spacing: 8px; padding: 5px 4px; }
QRadioButton::indicator { width: 16px; height: 16px; border-radius: 9px; border: 2px solid #86b995; background: white; }
QRadioButton::indicator:hover { border-color: #38a169; background: #eef9f1; }
QRadioButton::indicator:checked {
    border: 2px solid #2f855a;
    background: qradialgradient(
        cx: 0.5, cy: 0.5, radius: 0.5,
        fx: 0.5, fy: 0.5,
        stop: 0 #2f855a,
        stop: 0.42 #2f855a,
        stop: 0.48 white,
        stop: 1 white
    );
}
QRadioButton:focus { color: #22543d; }
QPushButton { background: #38a169; color: white; border: none; border-radius: 9px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #2f855a; }
QPushButton:pressed { background: #276749; }
QPushButton:disabled { background: #a9c9b1; }
QPushButton#secondary { background: #e5f4e8; color: #276749; }
QPushButton#danger { background: #fff0f0; color: #b83232; border: 1px solid #f1b7b7; }
QListWidget { background: white; border: 1px solid #cbe5d1; border-radius: 12px; padding: 5px; outline: none; }
QListWidget::item { padding: 11px; border-bottom: 1px solid #edf5ef; }
QListWidget::item:selected { background: #d7f0dd; color: #22543d; border-radius: 7px; }
QGroupBox { border: 1px solid #d4e8d9; border-radius: 10px; margin-top: 10px; padding: 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QProgressBar { border: none; border-radius: 8px; background: #e2efe5; text-align: center; min-height: 20px; }
QProgressBar::chunk { border-radius: 8px; background: #48bb78; }
"""
