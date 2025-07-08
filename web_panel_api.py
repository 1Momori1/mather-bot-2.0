from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import get_bots, get_bot_by_id, add_local_bot, add_ssh_bot, delete_bot, update_bot_status, update_bot_schedule
from local_utils import start_local_bot, stop_local_bot, get_local_bot_log
from ssh_utils import start_ssh_bot, stop_ssh_bot, get_ssh_bot_log
import uvicorn

app = FastAPI()

class BotCreate(BaseModel):
    name: str
    script_path: str
    type: str
    host: str = None
    port: int = None
    user: str = None
    password: str = None
    ssh_key_path: str = None
    group_name: str = None
    schedule: str = None

@app.get('/bots')
def list_bots():
    bots = get_bots()
    return [
        {
            'id': b[0], 'name': b[1], 'script_path': b[2], 'status': b[3], 'type': b[4],
            'host': b[5], 'port': b[6], 'user': b[7], 'ssh_key_path': b[8], 'group_name': b[9], 'schedule': b[10]
        } for b in bots
    ]

@app.post('/bots')
def create_bot(bot: BotCreate):
    if bot.type == 'local':
        add_local_bot(bot.name, bot.script_path, bot.group_name, bot.schedule)
    else:
        add_ssh_bot(bot.name, bot.script_path, bot.host, bot.port, bot.user, bot.password, bot.ssh_key_path, bot.group_name, bot.schedule)
    return {'ok': True}

@app.delete('/bots/{bot_id}')
def remove_bot(bot_id: int):
    delete_bot(bot_id)
    return {'ok': True}

@app.post('/bots/{bot_id}/start')
def start(bot_id: int):
    bot = get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(404)
    if bot[4] == 'local':
        start_local_bot(bot[2])
    else:
        start_ssh_bot(bot[5], bot[6], bot[7], bot[8], bot[2], bot[9])
    update_bot_status(bot_id, 'running')
    return {'ok': True}

@app.post('/bots/{bot_id}/stop')
def stop(bot_id: int):
    bot = get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(404)
    if bot[4] == 'local':
        stop_local_bot(bot[1])
    else:
        stop_ssh_bot(bot[5], bot[6], bot[7], bot[8], bot[1], bot[9])
    update_bot_status(bot_id, 'stopped')
    return {'ok': True}

@app.get('/bots/{bot_id}/log')
def get_log(bot_id: int):
    bot = get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(404)
    if bot[4] == 'local':
        log = get_local_bot_log(bot[2])
    else:
        log = get_ssh_bot_log(bot[5], bot[6], bot[7], bot[8], bot[2], bot[9])
    return {'log': log}

@app.post('/bots/{bot_id}/schedule')
def set_schedule(bot_id: int, schedule: str):
    update_bot_schedule(bot_id, schedule)
    return {'ok': True}

if __name__ == '__main__':
    uvicorn.run('web_panel_api:app', host='0.0.0.0', port=8000, reload=True) 