from dataclasses import dataclass


@dataclass(slots=True)
class Word:
    word: str
    translation: str
    level: str = "medium"
    learned: bool = False
    category: str = "other"
    image_url: str = ""
    id: int | None = None
