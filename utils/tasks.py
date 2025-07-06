from celery import Celery
import asyncio
import aiohttp

from utils.utils import get_files, send_files_message


app = Celery(
    'tasks',
    broker='redis://redis:6378/0',
    backend='redis://redis:6378/0'
)

app.autodiscover_tasks(['tasks'])


async def async_delete(url):
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as response:
            return response.status


@app.task
def cleanup_session(user_id: str):
    """Задача для очистки сессии: удаляет директорию и контейнер."""

    delete_directory_url = f"https://opensci.ru/delete-directory/{user_id}"
    delete_container_url = f"https://opensci.ru/delete/{user_id}"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_delete(delete_directory_url))
    loop.run_until_complete(async_delete(delete_container_url))


@app.task
def process_files(user_id: str, callback):
    """Задача для получения файлов и отправки сообщения."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        files = loop.run_until_complete(get_files(user_id))
        loop.run_until_complete(send_files_message(files, callback))
    finally:
        loop.close()


async def schedule_send_files(session_length: int, user_id: str, callback):
    """Задача для получения файлов и отправки сообщения."""
    await asyncio.sleep(session_length * 60)
    
    files = await get_files(user_id)

    await callback.message.answer("Ваша сессия завершилась, вот все файлы, которые были сохранены")

    await send_files_message(files, callback)
