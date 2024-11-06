from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import os, json, asyncio, importlib

# Modelo de task
class TaskModel(BaseModel):
    task: str
    status: int = 1
    cron: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

api = FastAPI()
# Cria o agendador assíncrono
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(api: FastAPI):
    scheduler.start()
    print("Agendador iniciado...")

    try:
        with open(file='index.json', mode='r', encoding='utf-8') as f:
            database = json.load(f)

        for i in database:
            if i.get('status'):
                se, mi, ho, da, we, mo = i.get('cron').split()
                scheduler.add_job(
                    importlib.import_module(f"tasks.{i.get('task')}").main,
                    trigger = CronTrigger(second=se, minute=mi, hour=ho, day=da, day_of_week=we, month=mo),
                    args    = i.get('args', []),
                    kwargs  = i.get('kwargs', {})
                )
                print(f"Agendado tarefa {i.get('task')} com o cron {i.get('cron')}.")

    except Exception as e:    
        print(e)

    yield

    scheduler.shutdown()

api.router.lifespan_context = lifespan

@api.get("/queue/")
async def read():
    jobs = scheduler.get_jobs()
    jobs_data = [
        {
            "job_id": job.id,
            "name": job.func.__module__.split('.')[-1], # Pega o nome do arquivo onde a função 'main' está definida, usando o módulo da função
            "next_run_time": job.next_run_time,  # O horário agendado para a próxima execução do job
            "trigger": str(job.trigger),  # O trigger associado ao job
            "misfire_grace_time": job.misfire_grace_time,  # Tempo de tolerância para atraso
            "args": job.args,  # Argumentos posicionais passados para a função
            "kwargs": job.kwargs,  # Argumentos nomeados passados para a função
        }
        for job in jobs
    ]
    return jobs_data

@api.post("/queue/pause")
async def pause(id: str):
    job = scheduler.get_job(id)

    if job:
        scheduler.pause_job(id)
        return {"message": f"Tarefa {id} pausada."}
    
    else:
        return {"message": f"Tarefa {id} não encontrada."}

@api.post("/queue/resume")
async def resume(id: str):
    job = scheduler.get_job(id)

    if job:
        scheduler.resume_job(id)
        return {"message": f"Tarefa {id} retomada."}
    
    else:
        return {"message": f"Tarefa {id} não encontrada."}

@api.get("/task/")
async def read():
    with open(file="index.json", mode="r", encoding="utf-8") as f:
        return json.load(f)

@api.post("/task/")
async def create(task: TaskModel):
    # Verifica se a tarefa existe no diretório 'tasks'
    found = False
    available = os.listdir('tasks')
    for i in available:
        if task.task == i.removesuffix('.py'):
            found = True
            break
    
    if not found:
        return {"message": f"Tarefa '{task.task}' não encontrada."}

    # Verifica se o status é válido (0 ou 1)
    if task.status not in [0, 1]:
        task.status = 1  # Define como 1 se o valor fornecido não for válido

    # Carrega o conteúdo do arquivo JSON ou inicia uma lista vazia se o arquivo não existir
    try:
        with open("index.json", mode="r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    # Adiciona a nova tarefa à lista carregada
    data.append(task.dict())  # Converte o objeto TaskModel para dicionário

    # Escreve o conteúdo atualizado no arquivo JSON
    with open("index.json", mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    se, mi, ho, da, we, mo = task.cron.split()

    scheduler.add_job(
        importlib.import_module(f"tasks.{task.task}").main,
                    trigger = CronTrigger(second=se, minute=mi, hour=ho, day=da, day_of_week=we, month=mo),
                    args    = task.args,
                    kwargs  = task.kwargs
                )

    return {"message": f"Tarefa '{task.task}' criada com sucesso.", "task": task.dict()}

@api.patch("/task/")
async def update(id: str, field: str, value):
    job = scheduler.get_job(id)

    if job:
        return {"message": f"Tarefa {id} retomada."}
    
    else:
        return {"message": f"Tarefa {id} não encontrada."}

@api.delete("/task/")
async def remove(id: str):
    job = scheduler.get_job(id)

    if job: 
        scheduler.remove_job(id)
        return {"message": f"Tarefa com ID '{id}' removida com sucesso."}

    else:
        return {"message": f"Tarefa {id} não encontrada."}