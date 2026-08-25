import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class ImageSignals(QObject):
    loaded = pyqtSignal(str, bytes)
    failed = pyqtSignal(str, str)


class SearchSignals(QObject):
    found = pyqtSignal(int, str)
    failed = pyqtSignal(int, str)


class ImageTask(QRunnable):
    def __init__(self, key: str, url: str):
        super().__init__()
        self.key = key
        self.url = url
        self.signals = ImageSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            request = Request(self.url, headers={"User-Agent": "LearnWords/2.0"})
            with urlopen(request, timeout=8) as response:
                data = response.read(5_000_000)
            self.signals.loaded.emit(self.key, data)
        except Exception as error:
            self.signals.failed.emit(self.key, str(error))


class ImageSearchTask(QRunnable):
    """Find a suitable word image through the Wikimedia Commons API."""

    ENDPOINT = "https://commons.wikimedia.org/w/api.php"

    def __init__(self, word_id: int, query: str):
        super().__init__()
        self.word_id = word_id
        self.query = query
        self.signals = SearchSignals()

    @pyqtSlot()
    def run(self) -> None:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": self.query,
            "gsrnamespace": "6",
            "gsrlimit": "8",
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": "900",
        }
        try:
            request = Request(
                f"{self.ENDPOINT}?{urlencode(params)}",
                headers={"User-Agent": "LearnWords/2.0 (educational desktop app)"},
            )
            with urlopen(request, timeout=10) as response:
                payload = json.load(response)
            pages = payload.get("query", {}).get("pages", {})
            candidates = sorted(pages.values(), key=lambda page: page.get("index", 999))
            for page in candidates:
                info = (page.get("imageinfo") or [{}])[0]
                if info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
                    continue
                image_url = info.get("thumburl") or info.get("url")
                if image_url:
                    self.signals.found.emit(self.word_id, image_url)
                    return
            self.signals.failed.emit(self.word_id, "Зображення не знайдено")
        except Exception as error:
            self.signals.failed.emit(self.word_id, str(error))
