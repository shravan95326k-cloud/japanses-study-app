import unittest

from app import Grammar, Kanji, Vocabulary, app, db


class StudyAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = app.app_context()
        cls.context.push()

    @classmethod
    def tearDownClass(cls):
        cls.context.pop()

    def setUp(self):
        self.client = app.test_client()
        self.client.get('/logout')

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

    def test_conversation_requires_login(self):
        self.assertEqual(self.client.get('/conversation').status_code, 302)
        self.assertEqual(self.client.post('/api/conversation', json={'message': 'こんにちは'}).status_code, 302)

    def test_conversation_modes_return_learning_content(self):
        email = 'conversation-test@example.com'
        self.client.post('/register', data={'email': email, 'password': 'testing123'})
        self.client.post('/login', data={'email': email, 'password': 'testing123'})

        chat = self.client.post('/api/conversation', json={'level': 'N4', 'mode': 'chat', 'message': '京都が好きです'})
        reading = self.client.post('/api/conversation', json={'level': 'N3', 'mode': 'reading', 'message': ''})
        correction = self.client.post('/api/conversation', json={'level': 'N5', 'mode': 'correct', 'message': '私わ学生です'})

        self.assertEqual(chat.status_code, 200)
        self.assertIn('reply', chat.get_json())
        self.assertIn('passage', reading.get_json())
        self.assertEqual(correction.get_json()['suggestions'][0]['corrected'], '私は')


if __name__ == '__main__':
    unittest.main()
