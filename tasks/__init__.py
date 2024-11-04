import os, sys, asyncio, pathlib, hashlib, datetime, importlib, functools

def task(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        hashlog = hashlib.sha256(f"{func.__module__.removeprefix('tasks.')}-{datetime.datetime.now()}".encode()).hexdigest()[:32]

        if not os.path.exists("tasks/log"):
            os.mkdir("tasks/log")

        if not os.path.exists(f"tasks/log/{func.__module__.removeprefix('tasks.')}"):
            os.mkdir(f"tasks/log/{func.__module__.removeprefix('tasks.')}")

        with open(f"tasks/log/{func.__module__.removeprefix('tasks.')}/{datetime.datetime.today().strftime('%Y%m%d%H%M%S')}.log", 'a', -1, 'utf-8') as f:

            f.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - INFO - {hashlog} - Running {func.__module__.removeprefix('tasks.')}...\n")

            f.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - INFO - {hashlog} - Args: {args}. Kwargs: {kwargs}.\n")

            if asyncio.iscoroutinefunction(func):
                r = await func(*args, **kwargs)
            else:
                r = func(*args, **kwargs)

            f.write(f"{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} - INFO - {hashlog} - Result from {func.__module__.removeprefix('tasks.')}: {r}.\n")
        return r
    return wrapper

__all__ = []

current = pathlib.Path(__file__).resolve().parent
sys.path.append(str(current))

for i in os.listdir(current):
    if i.endswith(".py") and i not in ("__init__.py", "__pycache__"):
        if hasattr(importlib.import_module(f"tasks.{i[:-3]}"), "main"):
            globals()[i[:-3]] = importlib.import_module(f"tasks.{i[:-3]}").main
            __all__.append(i[:-3])

