import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class ValidationSignals(QObject):
    finished = pyqtSignal(bool, bool, str)


class WordValidationTask(QRunnable):
    """Check exact entries in English and Ukrainian Wiktionary."""

    def __init__(self, word: str, translation: str):
        super().__init__()
        self.word = word
        self.translation = translation
        self.signals = ValidationSignals()

    @staticmethod
    def _exists(language: str, value: str) -> bool:
        params = urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "redirects": "1", "titles": value,
        })
        request = Request(
            f"https://{language}.wiktionary.org/w/api.php?{params}",
            headers={"User-Agent": "LearnWords/2.0 (educational desktop app)"},
        )
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
        pages = payload.get("query", {}).get("pages", [])
        return bool(pages and "missing" not in pages[0] and "invalid" not in pages[0])

    @pyqtSlot()
    def run(self) -> None:
        try:
            word_exists = self._exists("en", self.word.casefold())
            translation_exists = self._exists("uk", self.translation.casefold())
            self.signals.finished.emit(word_exists, translation_exists, "")
        except Exception as error:
            # A network problem must not prevent the user from working offline.
            self.signals.finished.emit(True, True, str(error))
