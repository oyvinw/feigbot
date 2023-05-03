import asyncio
import src


if __name__ == "__main__":
    print("hello from main")
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