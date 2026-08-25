import tempfile
import unittest
from pathlib import Path

from app.database import DuplicateWordError, WordRepository
from app.models import Word


class WordRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository = WordRepository(Path(self.temp_dir.name) / "words.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_read_mark_and_delete(self):
        word_id = self.repository.add(Word("apple", "яблуко"))
        self.assertEqual(self.repository.all()[0].translation, "яблуко")
        self.repository.mark_learned(word_id)
        self.assertEqual(self.repository.stats(), (1, 1))
        self.repository.update_image(word_id, "https://example.test/apple.jpg")
        self.assertEqual(self.repository.all()[0].image_url, "https://example.test/apple.jpg")
        self.repository.delete(word_id)
        self.assertEqual(self.repository.stats(), (0, 0))

    def test_duplicate_is_case_insensitive(self):
        self.repository.add(Word("Apple", "яблуко"))
        with self.assertRaises(DuplicateWordError):
            self.repository.add(Word("apple", "інший переклад"))

if __name__ == "__main__":
    unittest.main()
