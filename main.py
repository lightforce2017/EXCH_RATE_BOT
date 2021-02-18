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
import matplotlib.pyplot as plt

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
from datetime import datetime, timedelta



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
        else: # 10 min is not passed
            if data['rl'] is not None:
                for i in data['rl']:
                    ms += i+': {:.2f}'.format(data['rl'][i])+'\n'
            else: ms = 'Data was not received. Try after several minutes'
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


# not the first user input
# /exchange $10 to CAD or /exchange 10 USD to CAD
@dp.message_handler(state = Form.rltime, commands=['exchange'])
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
                    now = datetime.now().timestamp()
                    async with state.proxy() as data:
                        if not islimit(data['rltime'], now): # 10 min is passed
                            await state.update_data(rltime = datetime.now().timestamp()) #renew timestamp
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
                            await message.reply(ms)
                        else: # 10 min is not passed
                            print('10 минут не прошло')
                            if data['rl'] is not None:
                                for i in data['rl']:
                                    if i == cur2:
                                        nval = float(data['rl'][i])*v
                                        ms += cur1+str(val)+' to '+cur2+' is {:.2f}'.format(nval)
                            else:
                                ms = 'Data was not received. Try after several minutes'
                            await message.reply(ms)
            else:
                ms = 'Invalid value of the second currency or it is not in the list'
                await message.reply(ms)
        else:
            ms = 'Invalid value of the first currency or it is not in the list'
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
                        data['rltime'] = datetime.now().timestamp() # save the time of the request
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
            

# user's first input
# /history USD/CAD
# /history USD/CAD for 7 days
@dp.message_handler(state = '*', commands=['history'])
async def process_list_command(message: types.Message, state: FSMContext):
    
    ms = '' #init ms for message
    if message.text == '/history':
        await message.reply('Input command with parameters, ex: \n/history USD/CAD')
    else:
        arguments = message.get_args()
        args = arguments.split(' ')
        cc = args[0]
        cur1 = cur2 = ''
        if cc.find('/') == -1: 
            await message.reply('Invalid currency delimiter. Must be /')    
        else:
            cct = cc.split('/')
            cur1 = cct[0]
            cur2 = cct[1]
            curr = CurList.split(',')
            if cur1 in CurList:
                if cur2 in CurList:
                    if len(args) == 1 or len(args) == 4:
                        if len(args) == 4:
                            try:
                                int(args[2])
                            except ValueError:
                                ms = 'Invalid amount'
                                await message.reply(ms)
                            else:
                                val = int(args[2])
                                if val > 14:
                                    await message.reply('Too big number, let\'s take 14')
                                    val = 14
                                if val < 1:
                                    await message.reply('Too small number, let\'s take 1')
                                    val = 1
                                if args[3].lower() != 'days':
                                    ms = 'Invalid request. I can show info only for several days.'
                                    await message.reply(ms)
                                else:
                                    async with state.proxy() as data:
                                        data['rhtime'] = datetime.now().timestamp() # save the time of the request
                                        lastdate = datetime.today().strftime('%Y-%m-%d')
                                        firstdate = (datetime.today() - timedelta(days=val)).strftime('%Y-%m-%d')
                                        #api.exchangeratesapi.io/history?start_at=2019-11-27&end_at=2019-12-03&base=USD&symbols=CAD
                                        response = requests.get("http://api.exchangeratesapi.io/history?start_at="+firstdate+"&end_at="+lastdate+"&base="+cur1+"&symbols="+cur2)
                                        ms = ''
                                        hdict = {}
                                        if response.status_code == 200:
                                            data['rh'] = response.json()['rates']
                                            print(data['rh'])
                                            #y = []
                                            #tick_label = []
                                            for i in data['rh']:
                                            #    print(r['rates'][i]['CAD'])
                                                #y.append(data['rh'][i]['CAD'])
                                                #tick_label.append(i)
                                                hdict[i] = data['rh'][i][cur2]
                                            print(hdict)
                                            shdict = dict(sorted(hdict.items()))
                                            print(shdict)
                                            tick_label = list(shdict.keys())
                                            y = list(shdict.values())
                                            x = list(range(1, len(y)+1))
                                            print(tick_label)
                                            print(x)
                                            print(y)
                                            plt.title(cur1+'/'+cur2+' '+str(val)+' Day History - '+lastdate)
                                            plt.xlabel('date')
                                            plt.ylabel('rate')
                                            plt.xticks(rotation=90)
                                            plt.plot(tick_label, y)
                                            #plt.bar(x, y, tick_label = tick_label, width = 0.8, color = ['red', 'green'])
                                            plt.savefig('viz.png')
                                            plt.clf()
                                            #plt.show()
                                            ms = 'график'
                                        else: 
                                            ms = 'Data was not received'
                                        print('Новый запрос или Уже прошло 10 минут')
                                        await Form.rhtime.set()
                                        await message.reply(ms)
                        else: #1 arg
                            val = 7
                            '''
                            async with state.proxy() as data:
                                data['rltime'] = datetime.now().timestamp() # save the time of the request
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
                                await Form.rhtime.set()
                                await message.reply(ms)'''
                    else:
                       await message.reply('Check your request and try again') 
                        
                    
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