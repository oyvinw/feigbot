import asyncio
import logging
import feigbot

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                feigbot.start()
            )
        )
    except KeyboardInterrupt:
        loop.run_until_complete(feigbot.close())
    finally:
        loop.close()