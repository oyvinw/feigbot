import asyncio
import datetime
import logging
import os

import src

print("hello from main")

if __name__ == "__main__":
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