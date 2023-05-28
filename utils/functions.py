import asyncio
import logging
import time

from datetime import datetime
from binance.client import AsyncClient

from config import bot, chat_id_dump, chat_id_pump, perc_deltas, time_frames


logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)
logging.getLogger("databases").disabled = True
tiker_list = []


async def pump_dump_signals(percent, time_delta):
    time_to_sleep = await wait(time_delta)
    logging.info(f'Wait for timeframe for {time_to_sleep} sec.')
    await asyncio.sleep(time_to_sleep)

    old_price_list = {}
    logging.info(f'Starting pump-dump. {percent} | {time_delta}')

    while True:
        start_func = time.time()
        logging.info(f'Check volatility {percent}% {time_delta} sec.')
        try:
            client = await AsyncClient.create()
            book = await client.futures_orderbook_ticker()
            if bool(old_price_list) is False:  # получаем прайс для сравнения
                logging.info(f'First launch {percent} | {time_delta}')
                for i in book:
                    symbol = i["symbol"]  # символ
                    price = i["askPrice"]  # цена
                    old_price_list[symbol] = {
                        "sybmol": symbol,
                        "price": price
                    }
            else:
                new_price_list = {}
                for i in book:
                    symbol = i["symbol"]  # символ
                    price = i["askPrice"]  # цена
                    new_price_list[symbol] = {
                        "symbol": symbol,
                        "price": price
                    }
                for k in old_price_list:
                    if k in new_price_list:
                        try:
                            old_price = float(old_price_list[k]["price"])
                            new_price = float(new_price_list[k]["price"])
                            delta = new_price - old_price
                            delta_perc = round(float((delta / old_price) * 100), 3)
                            if abs(delta_perc) > percent:
                                if delta_perc > 0:
                                    text = f'✅ `{k}` is *PUMPING! +{delta_perc}%* in {time_delta} sec.\n' \
                                           f'*Current price*: {new_price}'
                                    await bot.send_message(chat_id=chat_id_pump, text=text, parse_mode='Markdown')
                                    logging.info(f'{k} | Found LONG')

                                elif delta_perc < 0:
                                    text = f'🩸 `{k}` is *DUMPING! {delta_perc}%* in {time_delta} sec.\n' \
                                           f'*Current price*: {new_price}'
                                    await bot.send_message(chat_id=chat_id_dump, text=text, parse_mode='Markdown')
                                    logging.info(f'{k} | Found SHORT')
                                else:
                                    pass

                        except Exception as err:
                            logging.error(f'{percent} | {time_delta} | {err}')
                            pass
                old_price_list = new_price_list
            end_func = time.time()
            func_duration = end_func - start_func
            time_charge = time_delta - func_duration
            await client.close_connection()
            await asyncio.sleep(time_charge)
        except Exception as err:
            logging.error(err)
            await asyncio.sleep(60)
            pass



async def wait(interval):
    date_now = datetime.now()
    time_now = datetime.strftime(date_now, "%H:%M:%S:%f")
    h_m_s_list = time_now.split(":")
    hours = h_m_s_list[0]
    if hours[0] == 0:
        hours = hours.replace("0", "")
    minutes = h_m_s_list[1]
    if minutes[0] == 0:
        minutes = minutes.replace("0", "")
    seconds = h_m_s_list[2]
    if seconds[0] == 0:
        seconds = seconds.replace("0", "")
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    miliseconds = int(h_m_s_list[3]) / 1000000

    if interval == 15:
        if seconds < 15:
            time_to_sleep = 15 - seconds - miliseconds
        else:
            time_to_sleep = 15 - seconds % 15 - miliseconds
    elif interval == 60:
        time_to_sleep = 60 - seconds - miliseconds
    elif interval == 300 or interval == 600:
        time_to_sleep = (4 - (minutes % 5)) * 60 + (60 - seconds) - miliseconds
    elif interval == 900:
        check = minutes % 15
        time_to_sleep = interval - check * 60 - seconds - miliseconds
    elif interval == 1800:
        check = minutes % 30
        time_to_sleep = interval - check * 60 - seconds - miliseconds
    elif interval == 3600:
        time_to_sleep = interval - minutes * 60 - seconds - miliseconds
    elif interval == 86400:
        time_to_sleep = interval - hours * 60 * 60 - minutes * 60 - seconds - miliseconds
    else:
        time_to_sleep = 60 - seconds - miliseconds
    return time_to_sleep




async def start_pump_dump():
    logging.info(f'Launching pump&dump announcer...')
    tasks = []
    for i in range(len(perc_deltas)):
        tasks.append(pump_dump_signals(percent=perc_deltas[i], time_delta=time_frames[i]))
    await asyncio.gather(*tasks)



async def test():
    pass


if __name__ == '__main__':
    print(asyncio.run(start_pump_dump()))
