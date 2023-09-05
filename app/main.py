from sanic import Sanic, Request, json, HTTPResponse, text
from sanic.log import logger
from psycopg_pool import AsyncConnectionPool
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
import redis.asyncio as redis

from orjson import loads, dumps
from models import PessoaCreate
from pydantic import ValidationError

import asyncio

WRITE_PESSOA_BATCH_SQL = "INSERT INTO pessoa (id, apelido, nome, nascimento, stack) VALUES (%(id)s, %(apelido)s, %(nome)s, %(nascimento)s, %(stack)s) ON conflict (apelido) do update set id = excluded.id, apelido = excluded.apelido, nome = excluded.nome, nascimento = excluded.nascimento, stack = excluded.stack"
CONSULTA_PESSOA_SQL = "SELECT id, apelido, nome, nascimento, stack FROM pessoa p WHERE p.id = %(id)s LIMIT 1"
BUSCA_PESSOA_SQL = "SELECT id, apelido, nome, nascimento, stack FROM pessoa p WHERE p.busca LIKE %s LIMIT 50"
COUNT_PESSOA_SQL = "SELECT count(*) FROM pessoa"


app = Sanic("Rinha", loads=loads, dumps=dumps)
class Cache:
    def __init__(self):
        self.pool = redis.ConnectionPool(host='redis', port=6379, db=0)

    async def set(self, key, value):
        client = redis.Redis(connection_pool=self.pool)
        await client.set(key, value)

    async def get(self, key):
        client = redis.Redis(connection_pool=self.pool)
        value = await client.get(key)
        return value.decode('utf-8') if value else None


@app.listener("before_server_start")
async def setup_pool(app, loop):
    global pool
    pool = AsyncConnectionPool(
        conninfo="postgresql://user:pass@db/rinha",
        max_size=40,
        min_size=40,
        max_idle=30,
    )

    global cache
    cache = Cache()


insert_queue = asyncio.Queue()


@app.listener("before_server_start")
async def setup_worker(app, loop):
    loop.create_task(worker())


@app.get("/")
async def get_health_status(request: Request):
    return json({"pai": "on"}, status=200)


@app.post("/pessoas")
async def create_pessoa(request: Request):
    try:
        pessoa = PessoaCreate(**request.json)
        if await cache.get(f"apelido:{pessoa.apelido}"):
            raise UniqueViolation

        await insert_queue.put(pessoa.model_dump())
        await cache.set(f"pessoa:{pessoa.id}", pessoa.model_dump_json())
        await cache.set(f"apelido:{pessoa.apelido}", "True")

        return HTTPResponse(status=201, headers={"location": f"/pessoas/{pessoa.id}"})

    except ValidationError:
        return HTTPResponse(status=400)
    except UniqueViolation:
        return HTTPResponse(status=422)
    except Exception as e:
        logger.error(e)
        return HTTPResponse(status=500)


@app.get("/pessoas/<id>")
async def get_pessoa_by_id(request: Request, id):
    async with pool.connection() as conn:
        if pessoa := await cache.get(f"pessoa:{id}"):
            return json(loads(pessoa), 200)
        cur = await conn.cursor(row_factory=dict_row).execute(
            CONSULTA_PESSOA_SQL, {"id": id}
        )
        if pessoa := await cur.fetchone():
            await cache.set(f"pessoa:{id}", dumps(pessoa))
            return json(pessoa, 200)
        else:
            return HTTPResponse(status=404)


@app.get("/pessoas")
async def get_pessoa_termo(request: Request):
    if not request.args:
        return HTTPResponse(status=400)
    if termo := request.args.get("t"):
        async with pool.connection() as conn:
            cur = await conn.cursor(row_factory=dict_row).execute(
                BUSCA_PESSOA_SQL, (f"%{termo}%",)
            )
            pessoas = await cur.fetchall()
            return json(pessoas, 200)
    else:
        return HTTPResponse(400)


@app.get("/contagem-pessoas")
async def get_count_pessoas(request: Request):
    async with pool.connection() as conn:
        cur = await conn.cursor().execute(COUNT_PESSOA_SQL)
        count = (await cur.fetchone())[0]
    return text(f"{count}", 200)


async def worker():
    batch_size = 100
    batch_timeout = 1

    while True:
        batch = []
        while len(batch) < batch_size:
            try:
                person = await asyncio.wait_for(
                    insert_queue.get(), timeout=batch_timeout
                )
                if person:
                    batch.append(person)
            except asyncio.TimeoutError:
                break
        if batch:
            await insert_into_db(batch)


async def insert_into_db(persons):
    async with pool.connection() as conn:
        async with conn.transaction() as t:
            cur = t.connection.cursor()
            await cur.executemany(WRITE_PESSOA_BATCH_SQL, persons)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, access_log=False)
