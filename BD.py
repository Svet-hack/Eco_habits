import sqlite3
con = sqlite3.connect('db.sqlite')
cur = con.cursor()
print("Таблицы:", cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
print("Пользователи:", cur.execute("SELECT * FROM users;").fetchall())
print("Задания:", cur.execute("SELECT * FROM tasks;").fetchall())
con.close()