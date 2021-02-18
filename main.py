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

# list of available currencies
CurList = 'CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN'
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


class Form(StatesGroup):
    rltime = State()
    rl = State()
    rhtime = State()
    rh = State()

def islimit(ts1, ts2):
    delta = ts2 - ts1
    min = delta / 60
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
  
# user's not the first input  
@dp.message_handler(state = Form.rltime, commands=['list', 'lst'])
async def process_list_command(message: types.Message, state: FSMContext):

    ms = '' #init ms for message
     
    now = datetime.now().timestamp()
    async with state.proxy() as data:
        if not islimit(data['rltime'], now): # 10 min is passed
            await state.update_data(rltime = datetime.now().timestamp()) #renew timestamp
            response = requests.get("http://api.exchangeratesapi.io/latest?base=USD")
            ms = ''
            if response.status_code == 200:
                data['rl'] = response.json()['rates']
                for i in data['rl']:
                    ms += i+': {:.2f}'.format(data['rl'][i])+'\n'
            else: ms = 'Data was not received'
        else:
            if data['rl'] is not None:
                for i in data['rl']:
                    ms += i+': {:.2f}'.format(data['rl'][i])+'\n'
            else: ms = 'Data was not received'
    print('Еще не прошло 10 минут')
    await message.reply(ms)
    
# user's first input
@dp.message_handler(state = '*', commands=['list', 'lst'])
async def process_list_command(message: types.Message, state: FSMContext):
    
    
    ms = '' #init ms for message

    async with state.proxy() as data:
        data['rltime'] = datetime.now().timestamp() #save the time of the request
        response = requests.get("http://api.exchangeratesapi.io/latest?base=USD")
        ms = ''
        if response.status_code == 200:
            data['rl'] = response.json()['rates']
            for i in data['rl']:
                ms += i+': {:.2f}'.format(data['rl'][i])+'\n'
        else: 
            ms = 'Data was not received'
    print('Новый запрос или Уже прошло 10 минут')
    await Form.rltime.set()
    await message.reply(ms)



            
            
# user's first input
# /exchange $10 to CAD or /exchange 10 USD to CAD
@dp.message_handler(state = '*', commands=['exchange'])
async def process_exc_command(message: types.Message, state: FSMContext):
    
    
    ms = '' #init ms for message
    
    if message.text == '/exchange':
        await message.reply('Input command with parameters, ex: \n/exchange 10 USD to CAD')
    else:
        arguments = message.get_args()
        args = arguments.split(' ')
        val = args[0]
        cur1 = cur2 = ''
        if val.find('$') > -1: 
            val = val[1:]
            cur1 = 'USD'
            cur2 = args[2]      
        else:
            cur1 = args[1]
            cur2 = args[3]
        curr = CurList.split(',')
        print(args)
        v = 1.0
        if cur1 in CurList:
            if cur2 in CurList:
                try:
                    float(val)
                except ValueError:
                    ms = 'Invalid amount'
                    await message.reply(ms)
                else:
                    v = float(val)
                    async with state.proxy() as data:
                        data['retime'] = datetime.now().timestamp() # save the time of the request
                        response = requests.get("http://api.exchangeratesapi.io/latest?base="+cur1)
                        ms = ''
                        if response.status_code == 200:
                            data['rl'] = response.json()['rates']
                            for i in data['rl']:
                                if i == cur2:
                                    print(data['rl'][i])
                                    nval = float(data['rl'][i])*v
                                    ms += cur1+str(val)+' to '+cur2+' is {:.2f}'.format(nval)
                        else: 
                            ms = 'Data was not received'
                        print('Новый запрос или Уже прошло 10 минут')
                        await Form.rltime.set()
                        await message.reply(ms)
            else:
                ms = 'Invalid value of the second currency or it is not in the list'
                await message.reply(ms)
        else:
            ms = 'Invalid value of the first currency or it is not in the list'
            await message.reply(ms)
            

       

    
@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text)
    
    
if __name__ == '__main__':
    executor.start_polling(dp)