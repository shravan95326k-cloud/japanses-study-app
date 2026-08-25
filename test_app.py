import unittest

from app import Grammar, Kanji, Vocabulary, app, db


class StudyAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = app.app_context()
        cls.context.push()
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.context.pop()

    def test_deck_counts_are_imported(self):
        self.assertGreaterEqual(Vocabulary.query.filter_by(level='N5').count(), 600)
        self.assertGreaterEqual(Vocabulary.query.filter_by(level='N4').count(), 600)
        self.assertGreaterEqual(Vocabulary.query.filter_by(level='N3').count(), 1700)
        self.assertEqual(Kanji.query.filter_by(level='N5').count(), 79)
        self.assertEqual(Kanji.query.filter_by(level='N4').count(), 166)
        self.assertEqual(Kanji.query.filter_by(level='N3').count(), 367)
        self.assertGreaterEqual(Grammar.query.filter_by(level='N5').count(), 100)

    def test_decks_require_login(self):
        for path in ('/study/vocabulary/N5', '/study/grammar/N3', '/study/kanji/N4', '/test/vocabulary/N5'):
            self.assertEqual(self.client.get(path).status_code, 302)

    def test_invalid_deck_is_not_found(self):
        self.assertEqual(self.client.get('/test/kanji/N1').status_code, 302)


if __name__ == '__main__':
    unittest.main()
