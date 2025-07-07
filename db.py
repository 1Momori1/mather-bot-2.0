import aiosqlite
import os
import shutil
from datetime import datetime

DB_PATH = 'bots.db'

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                script_path TEXT NOT NULL,
                token TEXT,
                status TEXT DEFAULT 'stopped',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_started TIMESTAMP,
                start_count INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

async def add_bot(name, script_path, token):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO bots (name, script_path, token) VALUES (?, ?, ?)', (name, script_path, token))
        await db.commit()

async def get_bots():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name, script_path, token, status, created_at, last_started, start_count FROM bots') as cursor:
            return await cursor.fetchall()

async def update_bot_status(bot_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        if status == 'running':
            await db.execute('''
                UPDATE bots 
                SET status = ?, last_started = CURRENT_TIMESTAMP, start_count = start_count + 1 
                WHERE id = ?
            ''', (status, bot_id))
        else:
            await db.execute('UPDATE bots SET status = ? WHERE id = ?', (status, bot_id))
        await db.commit()

async def delete_bot(bot_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
        await db.commit()

async def get_bot_by_id(bot_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT id, name, script_path, token, status, created_at, last_started, start_count FROM bots WHERE id = ?', (bot_id,)) as cursor:
            return await cursor.fetchone()

async def get_bot_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        # Общая статистика
        async with db.execute('SELECT COUNT(*) FROM bots') as cursor:
            result = await cursor.fetchone()
            total_bots = result[0] if result else 0
        
        async with db.execute('SELECT COUNT(*) FROM bots WHERE status = "running"') as cursor:
            result = await cursor.fetchone()
            running_bots = result[0] if result else 0
        
        async with db.execute('SELECT COUNT(*) FROM bots WHERE status = "stopped"') as cursor:
            result = await cursor.fetchone()
            stopped_bots = result[0] if result else 0
        
        # Самый активный бот
        async with db.execute('SELECT name, start_count FROM bots ORDER BY start_count DESC LIMIT 1') as cursor:
            most_active = await cursor.fetchone()
        
        return {
            'total_bots': total_bots,
            'running_bots': running_bots,
            'stopped_bots': stopped_bots,
            'most_active': most_active
        }

async def backup_database():
    """Создание резервной копии базы данных"""
    if not os.path.exists(DB_PATH):
        return False
    
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{backup_dir}/bots_backup_{timestamp}.db'
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        return backup_path
    except Exception as e:
        print(f"Ошибка создания резервной копии: {e}")
        return False

async def get_recent_activity(limit=10):
    """Получение последней активности ботов"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT name, status, last_started, start_count 
            FROM bots 
            WHERE last_started IS NOT NULL 
            ORDER BY last_started DESC 
            LIMIT ?
        ''', (limit,)) as cursor:
            return await cursor.fetchall() 