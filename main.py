import asyncio
import logging

from utils.functions import start_pump_dump

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)
logging.getLogger("databases").disabled = True
logging.getLogger("db").disabled = True


async def launch():
    tasks = [start_pump_dump()]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(launch())

