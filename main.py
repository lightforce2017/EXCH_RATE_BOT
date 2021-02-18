from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.types import ParseMode, InputMediaPhoto, ChatActions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import requests

##### DELETE in PRODUCTION
import json

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)
#####

from conf import TOKEN
from datetime import datetime



bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class State(StatesGroup):
    reqtime = State()
    req = State()


def islimit(ts1, ts2):
    delta = ts2 - ts1
    min = delta.total_seconds() / 60
    return min < 10.00
    

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет!\nИспользуй /help, '
                        'чтобы узнать список доступных команд!')
                        


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text(bold('Я могу ответить на следующие команды:'),
               '/list', '/lst', '/exchange', '/history', sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)

'''все сообщения при нулевом состоянии
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)
   '''
   
@dp.message_handler(state = '*', commands=['list', 'lst'])
async def process_list_command(message: types.Message, state: FSMContext):
    state = await state.get_state()
    ms = '' #init ms for message
    if state is None: # first user input
        await State.req.set()   # set any state to know that user got request
        async with state.proxy() as data:
            data['reqtime'] = datetime.datetime.now().timestamp() #save the time of the request
            response = requests.get("http://api.exchangeratesapi.io/latest?base=USD")
            ms = ''
            if response.status_code == 200:
                data['req'] = response.json()['rates']
                for i in data['req']:
                    ms += i+': {:.2f}'.format(rts[i])+'\n'
            else: ms = 'Data was not received'
    else:   # not the first user input
        now = datetime.datetime.now().timestamp()
        async with state.proxy() as data:
            if not islimit(data['reqtime'], now): # 10 min is passed
                data['reqtime'] = datetime.datetime.now().timestamp() #renew timestamp
                response = requests.get("http://api.exchangeratesapi.io/latest?base=USD")
                ms = ''
                if response.status_code == 200:
                    data['req'] = response.json()['rates']
                    for i in data['req']:
                        ms += i+': {:.2f}'.format(rts[i])+'\n'
                else: ms = 'Data was not received'
            else:
                if data['req'] is not None:
                    for i in data['req']:
                        ms += i+': {:.2f}'.format(rts[i])+'\n'
                else: ms = 'Data was not received'

    await message.reply(ms)
    
    
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)
    
    
if __name__ == '__main__':
    executor.start_polling(dp)