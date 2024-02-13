import sqlite3

conn = sqlite3.connect("user_credentials.db")
cursor = conn.cursor()

sql = '''
DROP TABLE IF EXISTS login_cred;
CREATE TABLE IF NOT EXISTS login_cred (
  id integer PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);
INSERT INTO login_cred (username, password) VALUES
  ('admin','admin'),
  ('user1','user1_pw'),
  ('user2','user2_pw'),
  ('user3','user3_pw')
'''
cursor.executescript(sql)
conn.commit()
conn.close()