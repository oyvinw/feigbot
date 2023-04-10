import asyncio
import datetime
import logging
import os

import src

print("hello from main")

if __name__ == "__main__":
    logpath = os.path.join(os.path.dirname(__file__), '../log')
    os.makedirs(logpath, exist_ok=True)

    date = '{date:%d-%m-%Y_%H-%M-%S}'.format(date=datetime.datetime.now())
    filepath = f'{logpath}/feigbot{date}.log'
    print(filepath)
    logging.basicConfig(filename=filepath,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

    logging.info("logging initialized")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                src.client.start()
            )
        )
    except KeyboardInterrupt:
        loop.run_until_complete(src.client.close())
    finally:
        loop.close()