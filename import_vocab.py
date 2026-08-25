"""Import a JLPT vocabulary CSV or JSON file into the app database.

Accepted fields: japanese (or word), reading, meaning (or english),
part_of_speech (or type), and example. Run with no argument to auto-discover
jlpt_n5-vocab.csv/json in this folder.
"""

import csv
import json
import sys
from pathlib import Path

from app import Vocabulary, app, db


def rows_from_file(path):
	if path.suffix.lower() == '.json':
		data = json.loads(path.read_text(encoding='utf-8'))
		return data if isinstance(data, list) else data.get('words', data.get('vocabulary', []))
	with path.open(newline='', encoding='utf-8-sig') as source:
		return list(csv.DictReader(source))


def value(row, *names):
	for name in names:
		if row.get(name):
			return str(row[name]).strip()
	return ''


def import_file(path):
	imported = 0
	skipped = 0
	for row in rows_from_file(path):
		japanese = value(row, 'japanese', 'word', 'term', 'kanji', 'Kanji', 'Hiragana')
		meaning = value(row, 'meaning', 'english', 'definition', 'translation', 'English Meaning')
		if not japanese or not meaning:
			skipped += 1
			continue
		word = Vocabulary.query.filter_by(japanese=japanese).first()
		if word is None:
			word = Vocabulary(japanese=japanese)
			db.session.add(word)
		word.reading = value(row, 'reading', 'kana', 'furigana', 'Hiragana', 'Furigana Format')
		word.meaning = meaning
		word.part_of_speech = value(row, 'part_of_speech', 'pos', 'type')
		word.example = value(row, 'example', 'sentence', 'Example')
		imported += 1
	db.session.commit()
	return imported, skipped


if __name__ == '__main__':
	candidates = [Path(sys.argv[1])] if len(sys.argv) > 1 else [
		Path('jlpt_n5-vocab.csv'), Path('jlpt_n5-vocab.json'),
	]
	source = next((path for path in candidates if path.exists()), None)
	if source is None:
		raise SystemExit('Place jlpt_n5-vocab.csv or .json in this folder, or pass its path.')
	with app.app_context():
		db.create_all()
		imported, skipped = import_file(source)
	print(f'Imported {imported} words from {source.name}; skipped {skipped} incomplete rows.')
