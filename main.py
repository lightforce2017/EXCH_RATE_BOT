from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ParseMode, InputMediaPhoto, InputMediaVideo, ChatActions
import requests

##### DELETE in PRODUCTION
import json

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)
#####

from conf import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет!\nИспользуй /help, '
                        'чтобы узнать список доступных команд!')


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text(bold('Я могу ответить на следующие команды:'),
               '/list', '/lst', '/exchange', '/history', sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['list', 'lst'])
async def process_photo_command(message: types.Message):
    response = requests.get("http://api.exchangeratesapi.io/latest?base=USD")
    ms = ''
    #### DELETE on Prod
    #print(response.status_code)
    #jprint(response.json())
    ####
    
    
    if response.status_code == 200:
        rts = response.json()['rates']
        for i in rts:
            ms += i+': {:.2f}'.format(rts[i])+'\n'
            #ms += i + ': '+str(int(( rts[i] * 100 ) + 0.5) / float(100))+'\n'
        print(ms)

    await message.reply(ms)
    
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)
    
    
if __name__ == '__main__':
    executor.start_polling(dp)