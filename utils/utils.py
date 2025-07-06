import os
import aiohttp
import tempfile
import zipfile
from aiogram.types import FSInputFile, InputMediaDocument


async def get_files(user_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://opensci.ru/download-files/{user_id}",
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            response.raise_for_status()
            zip_content = await response.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
        temp_zip.write(zip_content)
        temp_zip_path = temp_zip.name

    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    files = []
    for root, _, filenames in os.walk(temp_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            files.append(file_path)

    os.unlink(temp_zip_path)

    return files


async def send_files_message(files, callback):
    if not files:
        await callback.message.answer("Файлы не найдены")
        return

    if len(files) == 1:
        file = FSInputFile(files[0], filename=os.path.basename(files[0]))
        await callback.message.answer_document(file)
    else:
        media_groups = []
        current_group = []
        
        for file_path in files[:50]:
            file = FSInputFile(file_path, filename=os.path.basename(file_path))
            current_group.append(InputMediaDocument(media=file))
            
            if len(current_group) == 10:
                media_groups.append(current_group)
                current_group = []
        
        if current_group:
            media_groups.append(current_group)
        
        for media_group in media_groups:
            await callback.message.answer_media_group(media=media_group)
    
    await callback.message.answer("✅ Все файлы успешно скачаны!")
