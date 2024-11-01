from . import task

@task
async def main(a, b):
    return a * b