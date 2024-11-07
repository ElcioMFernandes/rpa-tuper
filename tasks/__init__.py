import os, asyncio, datetime, functools, hashlib

def task(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not os.path.isdir(os.path.join(__file__.removesuffix(os.path.basename(__file__)), 'log')):
            os.makedirs(os.path.join(__file__.removesuffix(os.path.basename(__file__)), 'log'), exist_ok=True)

        if not os.path.isdir(os.path.join(__file__.removesuffix(os.path.basename(__file__)), 'log', func.__module__.split('.')[-1])):
            os.makedirs(os.path.join(__file__.removesuffix(os.path.basename(__file__)), 'log', func.__module__.split('.')[-1]), exist_ok=True)

        with open(os.path.join(__file__.removesuffix(os.path.basename(__file__)), 'log', func.__module__.split('.')[-1], f"{datetime.datetime.now().strftime('%d%m%Y')}.log"),
                  mode="a",
                  encoding="utf-8") as l:
            l.write("Início.\n")

            if asyncio.iscoroutinefunction(func):
                r = await func(*args, **kwargs)
            else:
                r = func(*args, **kwargs)

            l.write("Fim.\n")
        return r
    return wrapper