import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from .database import WordRepository
from .main_window import MainWindow
from .styles import APP_STYLE


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("Learn Words")
    app.setStyleSheet(APP_STYLE)
    root = Path(__file__).resolve().parent.parent
    try:
        repository = WordRepository(root / "data" / "words.db")
        repository.import_json_once(root / "words_data.json")
        window = MainWindow(repository)
        window.show()
        return app.exec()
    except Exception as error:
        logging.exception("Application startup failed")
        QMessageBox.critical(None, "Помилка запуску", f"Не вдалося запустити програму:\n{error}")
        return 1
