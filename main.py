from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, responses
from typing import List, Dict, Any, Optional
import os, json, asyncio, importlib

# Modelo de task
class TaskModel(BaseModel):
    name: str
    task: str
    status: int = 1
    cron: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)

# Cria a API com FastAPI
api = FastAPI()

# Cria o agendador assíncrono
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(api: FastAPI):
    scheduler.start()
    print("Agendador iniciado...")
    try:
        # Limpa todas as tarefas antes de adicionar novamente
        scheduler.remove_all_jobs()

        with open(file='index.json', mode='r', encoding='utf-8') as f:
            database = json.load(f)

        for i in database:
            if i.get('status'):
                se, mi, ho, da, we, mo = i.get('cron').split()
                scheduler.add_job(
                    importlib.import_module(f"tasks.{i.get('task')}").main,
                    trigger = CronTrigger(second=se, minute=mi, hour=ho, day=da, day_of_week=we, month=mo),
                    id      = i.get('name'),
                    args    = i.get('args', []),
                    kwargs  = i.get('kwargs', {})
                )
                print(f"Agendado tarefa {i.get('task')} com o cron {i.get('cron')}.")

    except Exception as e:    
        print(e)

    try:
        yield
    finally:
        scheduler.remove_all_jobs()
        scheduler.shutdown(wait=False)

api.router.lifespan_context = lifespan

# Retorna a lista de tarefas na queue
@api.get("/queue/{task_id}")
@api.get("/queue/")
async def read(task_id: Optional[str] = None):
    if task_id:
        job = scheduler.get_job(task_id)

        if job:
            return responses.JSONResponse(
                content={
                    "status": "success",
                    "message": "Task details retrieved",
                    "task": {
                        "task_id": job.id,
                        "task_file": job.func.__module__.split('.')[-1],
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                        "args": job.args,
                        "kwargs": job.kwargs,       
                    }                
                }
            )
      
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "failure",
                    "message": "Task not found",
                    "task_id": task_id,
                }
            )

    # Coleta informações de todas as tarefas
    jobs = scheduler.get_jobs()
    jobs_data = [
        {
            "task_id": job.id,
            "task_file": job.func.__module__.split('.')[-1],
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "args": job.args,
            "kwargs": job.kwargs,
        }
        for job in jobs
    ]

    # Retorna a lista de tarefas em um JSON estruturado
    return responses.JSONResponse(
        content={
            "status": "success",
            "message": "List of all tasks",
            "tasks": jobs_data
        }
    )

# Pausar uma tarefa por tempo indeterminado ou até que seja reiniciado o scheduler
@api.get("/queue/{task_id}/pause/")
async def pause(task_id: str):
    job = scheduler.get_job(task_id)
    
    if job:
        if job.next_run_time is None:
            return responses.JSONResponse(
                status_code = 200,
                content = {
                        "detail": {
                        "status": "success",
                        "message": f"Task is already paused",
                        "task_id": task_id,
                        "paused": True
                    }                   
                }
            )

        else:
            scheduler.pause_job(task_id)
            return responses.JSONResponse(
                status_code = 200,
                content = {
                        "detail": {
                        "status": "success",
                        "message": f"Task paused",
                        "task_id": task_id,
                        "paused": True
                    }                   
                }
            )

    else:
        raise HTTPException(
            status_code = 404,
            detail = {
                "status": "failure",
                "message": f"Task not found",
                "task_id": task_id,
                "paused": False
            }
        )

# Retomar a execução de uma tarefa
@api.get("/queue/{task_id}/resume/")
async def resume(task_id: str):
    job = scheduler.get_job(task_id)

    if job:
        if job.next_run_time is None:
            scheduler.resume_job(task_id)
            return responses.JSONResponse(
                status_code = 200,
                content = {
                        "detail": {
                        "status": "success",
                        "message": f"task running",
                        "task_id": task_id,
                        "resumed": True
                    }                   
                }
            )
        else:
            return responses.JSONResponse(
                status_code = 200,
                content = {
                        "detail": {
                        "status": "success",
                        "message": f"The task is already running",
                        "task_id": task_id,
                        "resumed": True
                    }                   
                }
            )            
    else:
        raise HTTPException(
            status_code = 404,
            detail = {
                "status": "failure",
                "message": f"Task not found",
                "task_id": task_id,
                "resumed": False
            }
        )

# Remover uma tarefa da queue
@api.delete("/queue/task/")
async def remove(task_id: str):
    job = scheduler.get_job(task_id)

    if job:
        scheduler.remove_job(task_id)
        return responses.JSONResponse(
            status_code = 200,
            content = {
                    "detail": {
                    "status": "success",
                    "message": f"Task removed",
                    "task_id": task_id,
                    "removed": True
                }                   
            }
        )    
    else:
        raise HTTPException(
            status_code = 404,
            detail = {
                "status": "failure",
                "message": f"Task not found",
                "task_id": task_id,
                "paused": False
            }
        )        

# Adiciona uma tarefa a queue - ENDPOINT INCOMPLETO
@api.post("/queue/task/")
async def create(id: str):
    jobs = scheduler.get_jobs()

    running = False

    for job in jobs:
        if id == job.id:
            running = True
            break
    
    if running:
        return {"message": f"Tarefa {id} já está na queue."}

    return {"message": f"Tarefa {id} adicionada na queue."}

# Retorna todas as tarefas disponíveis - ENDPOINT PRONTO
@api.get("/task/")
async def read():
    with open(file="index.json", mode="r", encoding="utf-8") as f:
        return json.load(f)

# Criar uma nova tarefa - ENDPOINT PRONTO
@api.post("/task/create/")
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

    exists = False

    for j in data:
        if task.name in j.get('name'):
            exists = True
            break

    if exists:
        return {"message": f"Tarefa '{task.task}' já existe com esse id {task.name}."}

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

# Atualiza valor de uma tarefa - ENDPOINT INCOMPLETO
@api.patch("/task/")
async def update(id: str, field: str, value):
    job = scheduler.get_job(id)

    if job:
        return {"message": f"Tarefa {id} retomada."}
    
    else:
        return {"message": f"Tarefa {id} não encontrada."}