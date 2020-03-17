import hashlib
import sqlite3
old = sqlite3.connect("cats.db")
new = sqlite3.connect("cats.new.db")

all_data = old.execute("SELECT * FROM CATS").fetchall()

new.execute("""
CREATE TABLE IF NOT EXISTS CATS(
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USER_ID INTEGER NOT NULL,
                UPLOAD_TIME INTEGER,
                DATA BLOB NOT NULL,
                CHECKSUM TEXT NOT NULL UNIQUE
            )
""")
try:
    new.execute("CREATE INDEX INDEX_ID ON CATS(ID)")
    new.execute("CREATE INDEX INDEX_USER_ID ON CATS(USER_ID)")
    new.execute("CREATE INDEX INDEX_CHECKSUM ON CATS(CHECKSUM)")
except Exception as ex:
    print(ex)
for id, user_id, upload_time, data in all_data:
    md5 = hashlib.md5()
    md5.update(data)
    checksum = md5.hexdigest()
    print(id, user_id, upload_time, checksum)
    try:
        new.execute("""INSERT INTO CATS VALUES (?,?,?,?,?)""", (
            id, user_id, upload_time, data, checksum
        ))
    except Exception as ex:
        print(ex)


old.close()
new.close()
