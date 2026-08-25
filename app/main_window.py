from __future__ import annotations

import random
import re
import sqlite3

from PyQt6.QtCore import Qt, QThreadPool, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QRadioButton, QTabWidget, QVBoxLayout, QWidget,
)

from .database import DuplicateWordError, WordRepository
from .image_loader import ImageSearchTask, ImageTask
from .models import Word
from .word_validator import WordValidationTask


CATEGORIES = {
    "Інше": "other", "Їжа": "food", "Транспорт": "transport",
    "Почуття": "feelings", "Медицина": "medicine", "Одяг": "clothes",
    "Технології": "technology", "Природа": "nature", "Тварини": "animals",
    "Подорожі": "travel", "Дім": "home", "Фінанси": "finance",
}


class MainWindow(QMainWindow):
    def __init__(self, repository: WordRepository):
        super().__init__()
        self.repository = repository
        self.words: list[Word] = []
        self.card_index = 0
        self.quiz_word: Word | None = None
        self.quiz_answer = ""
        self.thread_pool = QThreadPool.globalInstance()
        self._image_tasks: set[ImageTask] = set()
        self._search_tasks: set[ImageSearchTask] = set()
        self._searching_word_ids: set[int] = set()
        self._validation_task: WordValidationTask | None = None
        self._pending_word: Word | None = None
        self.setWindowTitle("Learn Words · Мій словник")
        self.setMinimumSize(780, 600)
        self.resize(920, 680)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._build_add_tab()
        self._build_cards_tab()
        self._build_quiz_tab()
        self._build_dictionary_tab()
        self._build_stats_tab()
        self.refresh_all()

    @staticmethod
    def _page(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(14)
        heading = QLabel(title)
        heading.setObjectName("title")
        caption = QLabel(subtitle)
        caption.setObjectName("subtitle")
        caption.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(caption)
        return page, layout

    def _build_add_tab(self) -> None:
        page, layout = self._page("Додати нове слово", "Заповніть пару слів. Пробіли по краях буде прибрано автоматично.")
        form_box = QGroupBox("Слово та переклад")
        form = QFormLayout(form_box)
        form.setSpacing(12)
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Наприклад: apple")
        self.word_input.setMaxLength(80)
        self.translation_input = QLineEdit()
        self.translation_input.setPlaceholderText("Наприклад: яблуко")
        self.translation_input.setMaxLength(120)
        self.level_combo = QComboBox()
        self.level_combo.addItem("Легкий", "easy")
        self.level_combo.addItem("Середній", "medium")
        self.level_combo.addItem("Складний", "hard")
        self.level_combo.setCurrentIndex(1)
        self.category_combo = QComboBox()
        for label, value in CATEGORIES.items():
            self.category_combo.addItem(label, value)
        learned_wrap = QWidget()
        learned_layout = QHBoxLayout(learned_wrap)
        learned_layout.setContentsMargins(0, 0, 0, 0)
        self.learned_no = QRadioButton("Ще вивчаю")
        self.learned_yes = QRadioButton("Уже знаю")
        self.learned_no.setChecked(True)
        learned_layout.addWidget(self.learned_no)
        learned_layout.addWidget(self.learned_yes)
        learned_layout.addStretch()
        form.addRow("Слово", self.word_input)
        form.addRow("Переклад", self.translation_input)
        form.addRow("Складність", self.level_combo)
        form.addRow("Категорія", self.category_combo)
        status_label = QLabel("Статус")
        status_label.setToolTip("Оберіть, чи вважаєте ви це слово вже вивченим")
        learned_wrap.setToolTip("«Ще вивчаю» — слово залишається в роботі; «Уже знаю» — слово враховується у прогресі")
        form.addRow(status_label, learned_wrap)
        layout.addWidget(form_box)
        self.add_status = QLabel("")
        self.add_status.setWordWrap(True)
        layout.addWidget(self.add_status)
        self.add_button = QPushButton("＋  Додати до словника")
        self.add_button.clicked.connect(self.add_word)
        layout.addWidget(self.add_button)
        layout.addStretch()
        self.word_input.returnPressed.connect(self.translation_input.setFocus)
        self.translation_input.returnPressed.connect(self.add_word)
        self.tabs.addTab(page, "＋ Додати")

    def _build_cards_tab(self) -> None:
        page, layout = self._page("Картки", "Переглядайте слова у власному темпі.")
        self.card_image = QLabel("Зображення відсутнє")
        self.card_image.setObjectName("imageCard")
        self.card_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_image.setMinimumHeight(290)
        layout.addWidget(self.card_image, 1)
        self.card_word = QLabel("—")
        self.card_word.setObjectName("title")
        self.card_word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_translation = QLabel("—")
        self.card_translation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.card_word)
        layout.addWidget(self.card_translation)
        nav = QHBoxLayout()
        previous = QPushButton("← Попереднє")
        previous.setObjectName("secondary")
        previous.clicked.connect(lambda: self.move_card(-1))
        next_button = QPushButton("Наступне →")
        next_button.clicked.connect(lambda: self.move_card(1))
        nav.addWidget(previous)
        nav.addWidget(next_button)
        layout.addLayout(nav)
        self.tabs.addTab(page, "Картки")

    def _build_quiz_tab(self) -> None:
        page, layout = self._page("Мінітест", "Оберіть правильний переклад. Правильна відповідь позначає слово як вивчене.")
        self.quiz_prompt = QLabel("Додайте слова, щоб почати")
        self.quiz_prompt.setObjectName("title")
        self.quiz_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.quiz_prompt)
        self.answer_group = QButtonGroup(self)
        self.answer_group.setExclusive(True)
        self.answer_buttons: list[QPushButton] = []
        for index in range(4):
            button = QPushButton("—")
            button.setMinimumHeight(46)
            button.clicked.connect(lambda checked=False, i=index: self.check_answer(i))
            self.answer_group.addButton(button, index)
            self.answer_buttons.append(button)
            layout.addWidget(button)
        self.quiz_feedback = QLabel("")
        self.quiz_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.quiz_feedback)
        layout.addStretch()
        self.tabs.addTab(page, "Тест")

    def _build_dictionary_tab(self) -> None:
        page, layout = self._page("Мій словник", "Шукайте слова та керуйте збереженими записами.")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔎  Пошук слова або перекладу")
        self.search_input.textChanged.connect(self.refresh_dictionary)
        layout.addWidget(self.search_input)
        self.word_list = QListWidget()
        self.word_list.itemDoubleClicked.connect(self.open_selected_card)
        self.word_list.currentItemChanged.connect(self._dictionary_selection_changed)
        layout.addWidget(self.word_list, 1)
        actions = QHBoxLayout()
        self.learn_button = QPushButton("✓  Позначити як вивчене")
        self.learn_button.clicked.connect(self.mark_selected_learned)
        self.delete_button = QPushButton("Видалити вибране")
        self.delete_button.setObjectName("danger")
        self.delete_button.clicked.connect(self.delete_selected)
        actions.addWidget(self.learn_button)
        actions.addWidget(self.delete_button)
        layout.addLayout(actions)
        self.tabs.addTab(page, "Словник")

    def _build_stats_tab(self) -> None:
        page, layout = self._page("Прогрес", "Короткий огляд вашого словника.")
        layout.addStretch()
        self.stats_total = QLabel("Усього слів: 0")
        self.stats_total.setObjectName("title")
        self.stats_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_learned = QLabel("Вивчено: 0")
        self.stats_learned.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat("%p% вивчено")
        self.stats_message = QLabel("Почніть із першого слова 🌱")
        self.stats_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_total)
        layout.addWidget(self.stats_learned)
        layout.addWidget(self.progress)
        layout.addWidget(self.stats_message)
        layout.addStretch()
        self.tabs.addTab(page, "Прогрес")

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.strip().split())

    def add_word(self) -> None:
        source = self._clean(self.word_input.text())
        translation = self._clean(self.translation_input.text())
        if len(source) < 1 or len(translation) < 1:
            self._form_error("Заповніть обидва поля.", self.word_input if not source else self.translation_input)
            return
        if source.casefold() == translation.casefold():
            self._form_error("Слово та переклад мають відрізнятися.", self.translation_input)
            return
        if any(ord(char) < 32 for char in source + translation):
            self._form_error("Текст містить неприпустимі символи.", self.word_input)
            return
        if not re.fullmatch(r"[A-Za-z][A-Za-z '\-]*", source):
            self._form_error("У полі «Слово» використовуйте англійські літери без цифр.", self.word_input)
            return
        if not re.fullmatch(r"[А-Яа-яІіЇїЄєҐґ][А-Яа-яІіЇїЄєҐґ '\-]*", translation):
            self._form_error("У полі «Переклад» використовуйте українські літери без цифр.", self.translation_input)
            return
        if self._looks_suspicious(source) or self._looks_suspicious(translation):
            self._form_error("Значення схоже на випадковий набір символів. Перевірте написання.", self.word_input)
            return

        self._pending_word = Word(source, translation, self.level_combo.currentData(),
                                  self.learned_yes.isChecked(), self.category_combo.currentData())
        self.add_button.setEnabled(False)
        self.add_button.setText("Перевіряю слово…")
        self.add_status.setStyleSheet("color: #5d7565;")
        self.add_status.setText("Перевірка у словнику…")
        task = WordValidationTask(source, translation)
        self._validation_task = task
        task.signals.finished.connect(self._validation_finished)
        self.thread_pool.start(task)

    @staticmethod
    def _looks_suspicious(value: str) -> bool:
        letters = "".join(char.casefold() for char in value if char.isalpha())
        if len(letters) < 2:
            return True
        if re.search(r"(.)\1\1", letters):
            return True
        vowels = set("aeiouyаеєиіїоуюя")
        return not any(char in vowels for char in letters)

    def _validation_finished(self, word_exists: bool, translation_exists: bool, network_error: str) -> None:
        self.add_button.setEnabled(True)
        self.add_button.setText("＋  Додати до словника")
        pending = self._pending_word
        self._pending_word = None
        self._validation_task = None
        if pending is None:
            return
        unknown = []
        if not word_exists:
            unknown.append(f"англійське слово «{pending.word}»")
        if not translation_exists:
            unknown.append(f"переклад «{pending.translation}»")
        if unknown:
            answer = QMessageBox.question(
                self, "Слово не знайдено",
                "Wiktionary не розпізнав " + " та ".join(unknown) +
                ".\n\nПеревірте написання. Зберегти запис попри це?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Save:
                self._form_error("Збереження скасовано — виправте слово або переклад.", self.word_input)
                return
        elif network_error:
            self.add_status.setText("Онлайн-перевірка недоступна; виконано локальну перевірку.")
        self._save_word(pending)

    def _save_word(self, pending: Word) -> None:
        try:
            word_id = self.repository.add(pending)
        except DuplicateWordError:
            self._form_error(f"Слово «{pending.word}» уже є у словнику.", self.word_input)
            return
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Помилка бази даних", f"Не вдалося зберегти слово:\n{error}")
            return
        self.add_status.setStyleSheet("color: #258044;")
        self.add_status.setText(f"✓ «{pending.word}» успішно додано")
        self.word_input.clear()
        self.translation_input.clear()
        self.word_input.setFocus()
        self.refresh_all()
        self._search_image(word_id, pending.word)

    def _form_error(self, message: str, widget: QLineEdit) -> None:
        self.add_status.setStyleSheet("color: #b83232;")
        self.add_status.setText(message)
        widget.setFocus()
        widget.selectAll()

    def refresh_all(self) -> None:
        try:
            self.words = self.repository.all()
            if self.card_index >= len(self.words):
                self.card_index = max(0, len(self.words) - 1)
            self.refresh_dictionary()
            self.show_card()
            self.new_quiz()
            self.refresh_stats()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Помилка бази даних", str(error))

    def refresh_dictionary(self) -> None:
        query = self.search_input.text().strip().casefold()
        self.word_list.clear()
        for word in self.words:
            if query and query not in word.word.casefold() and query not in word.translation.casefold():
                continue
            marker = "✓" if word.learned else "○"
            item = QListWidgetItem(f"{marker}  {word.word}  —  {word.translation}")
            item.setData(Qt.ItemDataRole.UserRole, word.id)
            item.setToolTip(f"Категорія: {word.category} · Рівень: {word.level}")
            self.word_list.addItem(item)
        self._dictionary_selection_changed(self.word_list.currentItem())

    def _dictionary_selection_changed(self, current: QListWidgetItem | None, _previous=None) -> None:
        has_selection = current is not None
        self.delete_button.setEnabled(has_selection)
        if not has_selection:
            self.learn_button.setEnabled(False)
            self.learn_button.setText("✓  Позначити як вивчене")
            return
        word_id = current.data(Qt.ItemDataRole.UserRole)
        selected = next((word for word in self.words if word.id == word_id), None)
        already_learned = bool(selected and selected.learned)
        self.learn_button.setEnabled(not already_learned)
        self.learn_button.setText("✓  Уже вивчено" if already_learned else "✓  Позначити як вивчене")

    def mark_selected_learned(self) -> None:
        item = self.word_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Нічого не вибрано", "Спочатку виберіть слово у списку.")
            return
        try:
            self.repository.mark_learned(item.data(Qt.ItemDataRole.UserRole))
            self.words = self.repository.all()
            self.refresh_dictionary()
            self.refresh_stats()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Помилка бази даних", f"Не вдалося змінити статус слова:\n{error}")

    def show_card(self) -> None:
        self.card_image.setPixmap(QPixmap())
        if not self.words:
            self.card_word.setText("Словник порожній")
            self.card_translation.setText("Додайте перше слово на вкладці «Додати»")
            self.card_image.setText("🌿")
            return
        word = self.words[self.card_index]
        self.card_word.setText(word.word)
        self.card_translation.setText(word.translation)
        if not word.image_url:
            self.card_image.setText("Пошук зображення у Wikimedia Commons…")
            self._search_image(word.id, word.word)
            return
        key = f"card:{word.id}"
        self.card_image.setText("Завантаження зображення…")
        task = ImageTask(key, word.image_url)
        self._image_tasks.add(task)
        task.signals.loaded.connect(self._image_loaded)
        task.signals.failed.connect(self._image_failed)
        task.signals.loaded.connect(lambda *_: self._image_tasks.discard(task))
        task.signals.failed.connect(lambda *_: self._image_tasks.discard(task))
        self.thread_pool.start(task)

    def _search_image(self, word_id: int, query: str) -> None:
        if word_id in self._searching_word_ids:
            return
        self._searching_word_ids.add(word_id)
        task = ImageSearchTask(word_id, query)
        self._search_tasks.add(task)
        task.signals.found.connect(self._image_found)
        task.signals.failed.connect(self._image_search_failed)
        task.signals.found.connect(lambda *_: self._search_tasks.discard(task))
        task.signals.failed.connect(lambda *_: self._search_tasks.discard(task))
        self.thread_pool.start(task)

    def _image_found(self, word_id: int, image_url: str) -> None:
        self._searching_word_ids.discard(word_id)
        try:
            self.repository.update_image(word_id, image_url)
            self.words = self.repository.all()
            if self.words and self.words[self.card_index].id == word_id:
                self.show_card()
        except sqlite3.Error as error:
            QMessageBox.warning(self, "Не вдалося зберегти зображення", str(error))

    def _image_search_failed(self, word_id: int, _message: str) -> None:
        self._searching_word_ids.discard(word_id)
        if self.words and self.words[self.card_index].id == word_id:
            self.card_image.setText("Зображення не знайдено · спробуйте ще раз пізніше")

    def _image_loaded(self, key: str, data: bytes) -> None:
        if not self.words or key != f"card:{self.words[self.card_index].id}":
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.card_image.setPixmap(pixmap.scaled(520, 290, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
        else:
            self.card_image.setText("Не вдалося прочитати зображення")

    def _image_failed(self, key: str, _message: str) -> None:
        if self.words and key == f"card:{self.words[self.card_index].id}":
            self.card_image.setText("Зображення недоступне · перевірте інтернет")

    def move_card(self, offset: int) -> None:
        if self.words:
            self.card_index = (self.card_index + offset) % len(self.words)
            self.show_card()

    def new_quiz(self) -> None:
        if not self.words:
            self.quiz_word = None
            self.quiz_prompt.setText("Додайте слова, щоб почати")
            for button in self.answer_buttons:
                button.setText("—")
                button.setEnabled(False)
            return
        self.quiz_word = random.choice(self.words)
        self.quiz_answer = self.quiz_word.translation
        alternatives = list(dict.fromkeys(
            word.translation for word in self.words if word.id != self.quiz_word.id
        ))
        random.shuffle(alternatives)
        fallback = ["інший варіант", "не знаю", "пропустити"]
        choices = [self.quiz_answer] + alternatives[:3]
        for value in fallback:
            if len(choices) >= 4:
                break
            if value.casefold() not in {choice.casefold() for choice in choices}:
                choices.append(value)
        random.shuffle(choices)
        self.quiz_prompt.setText(f"Як перекладається «{self.quiz_word.word}»?")
        self.quiz_feedback.clear()
        for button, choice in zip(self.answer_buttons, choices):
            button.setText(choice)
            button.setEnabled(True)

    def check_answer(self, index: int) -> None:
        if self.quiz_word is None:
            return
        correct = self.answer_buttons[index].text() == self.quiz_answer
        if correct:
            try:
                self.repository.mark_learned(self.quiz_word.id)
                self.quiz_feedback.setStyleSheet("color: #258044; font-weight: 600;")
                self.quiz_feedback.setText("Правильно! ✓")
                self.words = self.repository.all()
                self.refresh_dictionary()
                self.refresh_stats()
            except sqlite3.Error as error:
                QMessageBox.critical(self, "Помилка бази даних", str(error))
                return
        else:
            self.quiz_feedback.setStyleSheet("color: #b83232; font-weight: 600;")
            self.quiz_feedback.setText(f"Не зовсім. Правильна відповідь: {self.quiz_answer}")
        for button in self.answer_buttons:
            button.setEnabled(False)
        QTimer.singleShot(1300, self.new_quiz)

    def open_selected_card(self, item: QListWidgetItem) -> None:
        word_id = item.data(Qt.ItemDataRole.UserRole)
        for index, word in enumerate(self.words):
            if word.id == word_id:
                self.card_index = index
                self.show_card()
                self.tabs.setCurrentIndex(1)
                break

    def delete_selected(self) -> None:
        item = self.word_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Нічого не вибрано", "Спочатку виберіть слово у списку.")
            return
        answer = QMessageBox.question(
            self, "Підтвердження", f"Видалити запис «{item.text()}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repository.delete(item.data(Qt.ItemDataRole.UserRole))
            self.refresh_all()
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Помилка бази даних", f"Не вдалося видалити слово:\n{error}")

    def refresh_stats(self) -> None:
        total, learned = self.repository.stats()
        percent = round(learned * 100 / total) if total else 0
        self.stats_total.setText(f"Усього слів: {total}")
        self.stats_learned.setText(f"Вивчено: {learned}")
        self.progress.setValue(percent)
        if total == 0:
            message = "Почніть із першого слова 🌱"
        elif percent == 100:
            message = "Усі слова вивчено — чудова робота! 🌟"
        elif percent >= 50:
            message = "Більша половина вже позаду!"
        else:
            message = "Регулярність важливіша за швидкість 🌿"
        self.stats_message.setText(message)
