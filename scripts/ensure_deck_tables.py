import sqlite3, os
os.makedirs("data", exist_ok=True)
con = sqlite3.connect("data/projects.sqlite")
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS decks(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, source TEXT, meta_json TEXT);""")
cur.execute("""CREATE TABLE IF NOT EXISTS deck_slides(id INTEGER PRIMARY KEY AUTOINCREMENT, deck_id INTEGER NOT NULL, slide_no INTEGER NOT NULL, kind TEXT, title TEXT, bullets_json TEXT, notes_json TEXT, FOREIGN KEY(deck_id) REFERENCES decks(id));""")
cur.execute("""CREATE TABLE IF NOT EXISTS style_profiles(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at INTEGER NOT NULL, name TEXT, profile_json TEXT);""")
con.commit(); con.close()
print("[OK] ensure_deck_tables.py: Schema ok")
