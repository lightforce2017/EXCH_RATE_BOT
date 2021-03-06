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
import os
from conf import TOKEN
from datetime import datetime, timedelta

# list of available currencies
CurList = 'CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN'

transl_com = ['.дшые','.дые','.учсрфтпу','.ршыещкн']


bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())



class Form(StatesGroup):
    rltime = State()
    rl = State()
    rhtime = State()
    rh = State()

def islimit(ts1, ts2):
    delta = ts2 - ts1
    min = delta / 60
    return min < 10.00
    
def translit(rutxt):
    transl_list =     'йцукенгшщзфывапролдячсмитьЙЦУКЕНГШЩЗФЫВАПРОЛДЯЧСМИТЬ.;'
    transl_dec_list = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM/$'
    for i in range(0, len(transl_list)):
        rutxt = rutxt.replace(transl_list[i],transl_dec_list[i])
    entxt = rutxt
    return entxt
    
    
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Hello!\nType /help, '
                        'to find how to use commands!')
                        


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    ms = """
    Whole list of commands:
/help - Get instructions about main commands

/list - returns list of all available rates

/lst - as /list,  returns list of all available rates

/exchange - converts to the second currency with two decimal precision and return. Examples: 
/exchange 10 USD to CAD
/exchange $10 to CAD

/history - return an image graph chart which shows the exchange rate graph/chart of the selected currency for the last N days.
Examples:
/history USD/CAD for 7 days
/history USD/CAD
In the second case it will show graph for the last 7 days"""
    
    await message.reply(ms)


  
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
            cur2 = args[2].upper()      
        else:
            cur1 = args[1].upper()
            cur2 = args[3].upper()
        curr = CurList.split(',')
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
                                        nval = float(data['rl'][i])*v
                                        ms += str(val)+ ' '+ cur1+' to '+cur2+' is {:.2f}'.format(nval)
                            else: 
                                ms = 'Data was not received'
                            await message.reply(ms)
                        else: # 10 min is not passed
                            if data['rl'] is not None:
                                for i in data['rl']:
                                    if i == cur2:
                                        nval = float(data['rl'][i])*v
                                        ms += str(val)+ ' '+ cur1+' to '+cur2+' is {:.2f}'.format(nval)
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
            cur2 = args[2].upper()     
        else:
            cur1 = args[1].upper()
            cur2 = args[3].upper()
        curr = CurList.split(',')
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
                                    nval = float(data['rl'][i])*v
                                    ms += str(val)+ ' '+ cur1+' to '+cur2+' is {:.2f}'.format(nval)
                        else: 
                            ms = 'Data was not received'
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
        await message.reply('Input command with parameters, ex: \n/history USD/CAD\nor\n/history USD/CAD for 7 days')
    else:
        arguments = message.get_args()
        args = arguments.split(' ')
        cc = args[0]
        cur1 = cur2 = ''
        if cc.find('/') == -1: 
            await message.reply('Invalid currency delimiter. Must be /')    
        else:
            cct = cc.split('/')
            cur1 = cct[0].upper()
            cur2 = cct[1].upper()
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
                                    lastdate = datetime.today().strftime('%Y-%m-%d')
                                    firstdate = (datetime.today() - timedelta(days=val)).strftime('%Y-%m-%d')
                                    #Ex: api.exchangeratesapi.io/history?start_at=2019-11-27&end_at=2019-12-03&base=USD&symbols=CAD
                                    response = requests.get("http://api.exchangeratesapi.io/history?start_at="+firstdate+"&end_at="+lastdate+"&base="+cur1+"&symbols="+cur2)
                                    ms = ''
                                    hdict = {}
                                    if response.status_code == 200:
                                        rh = response.json()['rates']
                                        for i in rh:
                                            hdict[i] = rh[i][cur2]
                                        shdict = dict(sorted(hdict.items()))
                                        tick_label = list(shdict.keys())
                                        y = list(shdict.values())
                                        x = list(range(1, len(y)+1))
                                        plt.title(cur1+'/'+cur2+' '+str(val)+' Day History - '+lastdate)
                                        plt.xlabel('date')
                                        plt.ylabel('rate')
                                        plt.xticks(rotation=90)
                                        plt.plot(tick_label, y)
                                        
                                        f = 'pics/viz'+str(message.from_user.id)+'.png'
                                        plt.savefig(f)
                                        plt.clf()

                                        await bot.send_photo(message.from_user.id, photo=open(f, 'rb'))
                                        if os.path.isfile(f):
                                            os.remove(f)
                                    else: 
                                        await message.reply('Data was not received')
                                        
                        else: #1 arg
                            val = 7
                            lastdate = datetime.today().strftime('%Y-%m-%d')
                            firstdate = (datetime.today() - timedelta(days=val)).strftime('%Y-%m-%d')
                            #Ex: api.exchangeratesapi.io/history?start_at=2019-11-27&end_at=2019-12-03&base=USD&symbols=CAD
                            response = requests.get("http://api.exchangeratesapi.io/history?start_at="+firstdate+"&end_at="+lastdate+"&base="+cur1+"&symbols="+cur2)
                            ms = ''
                            hdict = {}
                            if response.status_code == 200:
                                rh = response.json()['rates']
                                for i in rh:
                                    hdict[i] = rh[i][cur2]
                                shdict = dict(sorted(hdict.items()))
                                tick_label = list(shdict.keys())
                                y = list(shdict.values())
                                x = list(range(1, len(y)+1))
                               
                                plt.title(cur1+'/'+cur2+' '+str(val)+' Day History - '+lastdate)
                                plt.xlabel('date')
                                plt.ylabel('rate')
                                plt.xticks(rotation=90)
                                plt.plot(tick_label, y)
                            
                                f = 'pics/viz'+str(message.from_user.id)+'.png'
                                plt.savefig(f)
                                plt.clf()

                                await bot.send_photo(message.from_user.id, photo=open(f, 'rb'))
                                if os.path.isfile(f):
                                    os.remove(f)
                            else: 
                                await message.reply('Data was not received')
                                
                    else:
                       await message.reply('Check your request and try again') 
                else:
                    ms = 'Invalid value of the second currency or it is not in the list'
                    await message.reply(ms)
            else:
                ms = 'Invalid value of the first currency or it is not in the list'
                await message.reply(ms)   


    
@dp.message_handler()
async def echo_message(message: types.Message):
    ms = 'Choose proper command.\nType /help for help'
    if message.text == 'хелп':
        ms = """Короче, смотри, как надо:
/list - выводит список всех валют, которые найдет на сайте

/lst - по сути то же самое, это если лень букву i искать

/exchange - быстро посчитает, сколько баксов в 100 рублях, но только если написать так: 
/exchange 100 RUB to USD
Если написать USD мелкими буквами - не проблема, а вот опечаток я не прощаю!
Впрочем, если тебе нужно по-быстрому обменять валюту, и хочешь посчитать, сколько рублей дадут за десятку баксов, можешь написать проще:
/exchange $10 to RUB
Почему нельзя наоборот, /exchange 100 RUB to $ ?
Потому что я забочусь о тебе, и ты можешь пропустить знак доллара, а я буду ломать голову, что это такое.

Погнали дальше

/history - никаких учебников истории или истории твоего Телеграма. Просто сводка по курсам валют за последнюю неделю.
Интересно? Тогда пиши
/history USD/RUB for 7 days
И нет, ты не можешь написать years вместо days, потому что это слишком даже для меня (да и зачем?)
Окей, теоретически ты можешь перехитрить меня и выбрать 0 и даже миллион дней, но по факту я дам тебе прогноз либо за 1, либо за 14 дней. Оно тебе надо?
И специально, если тебе неохота писать это #for 7 days#, можешь не писать:
/history USD/RUB
Я тогда сделаю сводку за последнюю неделю, потому что 7 - мое любимое число.
И да, я не говорил, что нарисую даже картинку по этой теме? Хе-хе, увидишь.

Кстати, пиши команды с /, а не с \, а то буду думать, что ты меня путаешь с кем-то."""
    if message.text.split(' ')[0] in transl_com:
        ms = 'I think, you wanted to input this:'
        await message.reply(ms)
        ms = translit(message.text)

    await message.reply(ms)
    #await bot.send_message(msg.from_user.id, msg.text)
    
    
if __name__ == '__main__':
    executor.start_polling(dp)