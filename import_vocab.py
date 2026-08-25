"""Import a JLPT vocabulary CSV or JSON file into the app database.

Accepted fields: japanese (or word), reading, meaning (or english),
part_of_speech (or type), and example. Run with no argument to auto-discover
jlpt_n5-vocab.csv/json in this folder.
"""

import csv
import json
import re
import sys
from pathlib import Path

from app import Grammar, Kanji, Vocabulary, app, db

DATA_DIR = Path(__file__).resolve().parent / 'data'


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


def import_level_vocab(path):
	imported = 0
	with path.open(newline='', encoding='utf-8-sig') as source:
		for row in csv.DictReader(source):
			japanese = value(row, 'word', 'japanese', 'kanji')
			meaning = value(row, 'meanings', 'meaning', 'English Meaning')
			if not japanese or not meaning:
				continue
			word = Vocabulary.query.filter_by(japanese=japanese).first()
			if word is None:
				word = Vocabulary(japanese=japanese)
				db.session.add(word)
			word.level = value(row, 'level').upper() or 'N5'
			word.reading = value(row, 'reading', 'kana')
			word.meaning = meaning
			word.example = value(row, 'example_ja', 'example', 'Example')
			imported += 1
	db.session.commit()
	return imported


def import_grammar(path):
	imported = 0
	with path.open(newline='', encoding='utf-8-sig') as source:
		for row in csv.DictReader(source):
			point = value(row, 'Grammar Point')
			if not point:
				continue
			level = value(row, 'JLPT Level').upper().replace('JLPT ', '')
			grammar = Grammar.query.filter_by(level=level, point=point).first()
			if grammar is None:
				grammar = Grammar(level=level, point=point)
				db.session.add(grammar)
			grammar.meaning = value(row, 'Meaning')
			grammar.formation = value(row, 'Formation')
			grammar.example_japanese = value(row, 'Example (Japanese)')
			grammar.example_english = value(row, 'Example (English)')
			imported += 1
	db.session.commit()
	return imported


def import_kanji(path, level):
	imported = 0
	for row in json.loads(path.read_text(encoding='utf-8')):
		character = value(row, 'character')
		if not character:
			continue
		kanji = Kanji.query.filter_by(level=level, character=character).first()
		if kanji is None:
			kanji = Kanji(level=level, character=character)
			db.session.add(kanji)
		kanji.meaning = value(row, 'meaning')
		kanji.readings = ', '.join(row.get('onYomi', []) + row.get('kunYomi', []))
		kanji.mnemonic = value(row, 'mnemonic')
		kanji.vocabulary = '; '.join(item.get('word', '') + ' (' + item.get('reading', '') + ')' for item in row.get('vocabulary', []))
		imported += 1
	db.session.commit()
	return imported


def import_kanji_csv(path):
	imported = 0
	with path.open(newline='', encoding='utf-8-sig') as source:
		for row in csv.DictReader(source):
			character = value(row, 'character')
			level = value(row, 'level').upper()
			if not character or level not in {'N5', 'N4', 'N3'}:
				continue
			kanji = Kanji.query.filter_by(level=level, character=character).first()
			if kanji is None:
				kanji = Kanji(level=level, character=character)
				db.session.add(kanji)
			kanji.meaning = value(row, 'meanings', 'meaning')
			kanji.readings = value(row, 'onyomi') + (', ' + value(row, 'kunyomi') if value(row, 'kunyomi') else '')
			imported += 1
	db.session.commit()
	return imported


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
		if len(sys.argv) > 1:
			source = Path(sys.argv[1])
			if 'grammar' in source.name.lower():
				print(f'Imported {import_grammar(source)} grammar cards.')
			else:
				imported, skipped = import_file(source)
				print(f'Imported {imported} vocabulary words; skipped {skipped} incomplete rows.')
		else:
			for source in sorted(DATA_DIR.glob('vocab-n*.csv')):
				print(f'Imported {import_level_vocab(source)} vocabulary cards from {source.name}.')
			for source in sorted(DATA_DIR.glob('kanji-n*.csv')):
				print(f'Imported {import_kanji_csv(source)} kanji cards from {source.name}.')
			for source in sorted(DATA_DIR.glob('hanabira_jlpt_n*_grammar.csv')):
				print(f'Imported {import_grammar(source)} grammar cards from {source.name}.')
			for source in sorted(DATA_DIR.glob('kanji-data-N*.json')):
				match = re.search(r'(N[345])', source.name.upper())
				if match:
					print(f'Imported {import_kanji(source, match.group(1))} kanji cards from {source.name}.')
			for source in [DATA_DIR / 'JLPT_N5_Vocabulary.csv', DATA_DIR / 'jlpt_n5-vocab.csv', DATA_DIR / 'jlpt_n5-vocab.json']:
				if source.exists():
					imported, skipped = import_file(source)
					print(f'Imported {imported} vocabulary words; skipped {skipped} incomplete rows.')
					break
