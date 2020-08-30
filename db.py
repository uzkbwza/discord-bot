import sqlite3

conn = sqlite3.connect('hmm.db', detect_types=sqlite3.PARSE_COLNAMES)
conn.row_factory = sqlite3.Row
