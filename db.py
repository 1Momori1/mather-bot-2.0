import sqlite3

DB_PATH = 'bots.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        script_path TEXT NOT NULL,
        status TEXT DEFAULT 'stopped',
        type TEXT DEFAULT 'local',
        host TEXT,
        port INTEGER,
        user TEXT,
        password TEXT,
        ssh_key_path TEXT,
        group_name TEXT,
        schedule TEXT
    )''')
    conn.commit()
    conn.close()

def add_local_bot(name, path, group_name=None, schedule=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO bots (name, script_path, type, group_name, schedule) VALUES (?, ?, ?, ?, ?)', (name, path, 'local', group_name, schedule))
    conn.commit()
    conn.close()

def add_ssh_bot(name, path, host, port, user, password=None, ssh_key_path=None, group_name=None, schedule=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO bots (name, script_path, type, host, port, user, password, ssh_key_path, group_name, schedule) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (name, path, 'ssh', host, port, user, password, ssh_key_path, group_name, schedule))
    conn.commit()
    conn.close()

def get_bots():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, script_path, status, type, host, port, user, ssh_key_path, group_name, schedule FROM bots')
    bots = c.fetchall()
    conn.close()
    return bots

def get_bot_by_id(bot_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    conn.close()
    return bot

def update_bot_status(bot_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE bots SET status = ? WHERE id = ?', (status, bot_id))
    conn.commit()
    conn.close()

def update_bot_schedule(bot_id, schedule):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE bots SET schedule = ? WHERE id = ?', (schedule, bot_id))
    conn.commit()
    conn.close()

def delete_bot(bot_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
    conn.commit()
    conn.close() 