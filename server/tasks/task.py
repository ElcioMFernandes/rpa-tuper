from . import task

# Definindo uma função assíncrona para executar como tarefa agendada
@task
async def main(*args, **kwargs):
    print(f"{kwargs['prefix']} {args[0]} {kwargs['sufix']}.")