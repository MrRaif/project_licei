
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from utils import encode, decode

# Укажите токен вашего бота
API_TOKEN = '6704240977:AAEMOlH8HjJqqp8mj1C-ll-t6BHC_bCP5hU'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class EncodeDecodeStates(StatesGroup):
    waiting_for_wav = State()
    waiting_for_text = State()

class Decode(StatesGroup):
    waiting_for_wav = State()


@dp.message_handler(commands=['cancel'], state='*')
async def cancel_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.answer('Действие отменено.')


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Введите /encode для кодирования\nВведите /decode для декодирования")


@dp.message_handler(commands=['encode'], state="*")
async def cmd_encode(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте WAV-файл для кодирования")
    await EncodeDecodeStates.waiting_for_wav.set()


@dp.message_handler(state=EncodeDecodeStates.waiting_for_wav, content_types=types.ContentTypes.DOCUMENT)
async def process_wav_file(message: types.Message, state: FSMContext):
    await message.answer("Получили файл, обрабатываем...")
    try:
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        file_path = f"temp_{file_id}.wav"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file.read())
        await state.update_data(file_path=file_path)
        await message.answer("Теперь введите строку для кодирования в WAV-файл")
        await EncodeDecodeStates.next()
    except Exception as e:
        print(e)
        await message.answer("Произошла ошибка.")
        await state.finish()


@dp.message_handler(state=EncodeDecodeStates.waiting_for_text)
async def process_text_to_encode(message: types.Message, state: FSMContext):
    await message.answer("Кодируем...")
    try:
        data = await state.get_data()
        file_path = data['file_path']
        text_to_encode = message.text
        encode(file_path, text_to_encode)
        with open('sampleStego.wav', 'rb') as encoded_file:
            await message.answer_document(encoded_file)
        os.remove(file_path)
        os.remove('sampleStego.wav')
        await message.answer("Успешно!")
        await state.finish()
    except Exception as e:
        print(e)
        await message.answer("Нам не удалось закодировать сообщение.")
        await state.finish()


@dp.message_handler(commands=['decode'], state="*")
async def cmd_decode(message: types.Message):
    await message.answer("Пожалуйста, отправьте WAV-файл для декодирования")
    await Decode.waiting_for_wav.set()


@dp.message_handler(state=Decode.waiting_for_wav, content_types=types.ContentTypes.DOCUMENT)
async def process_wav_file_to_decode(message: types.Message, state: FSMContext):
    await message.answer("Получили файл, пробуем раскодировать...")
    try:
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        file_path = f"temp_{file_id}.wav"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file.read())
        decoded_text = decode(file_path)
        await message.answer(decoded_text)
        os.remove(file_path)
        await state.finish()
    except Exception as e:
        print(e)
        await message.answer("Нам не удалось раскодировать сообщение.")
        await state.finish()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)