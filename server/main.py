from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, responses, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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

connected_clients = List[WebSocket] = []

# Configuração de CORS para permitir o frontend React
origins = [
    "http://localhost:5173",  # URL do seu frontend React
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Permite apenas as origens especificadas
    allow_credentials=True,
    allow_methods=["*"],            # Permite todos os métodos (GET, POST, etc)
    allow_headers=["*"],            # Permite todos os cabeçalhos
)

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
        scheduler.shutdown(wait=True)

api.router.lifespan_context = lifespan

@api.webhooks("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

async def notify_clients(message: str):
    for client in connected_clients:
        await client.send_text(message)

@api.get("/queue/")          # Retorna a lista de tarefas na queue
@api.get("/queue/{task_id}") # Retorna uma tarefa da queue, se existir
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

@api.get("/queue/{task_id}/pause/") # Pausar uma tarefa por tempo indeterminado ou até que seja reiniciado o scheduler
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

@api.get("/queue/{task_id}/resume/") # Retomar a execução de uma tarefa
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

@api.delete("/queue/") # Remover uma tarefa da queue
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
                "removed": False
            }
        )

@api.post("/queue/") # Adiciona uma tarefa na queue
async def create(task_id: str):
    job = scheduler.get_job(task_id)

    if job:
        return responses.JSONResponse(
            status_code = 200,
            content = {
                    "detail": {
                    "status": "success",
                    "message": f"Task already exists",
                    "task_id": task_id,
                    "created": False
                }                   
            }
        )
    
    else:
        with open(file = "index.json", mode = "r", encoding = "utf-8") as f:
            data = json.load(f)

        for i in data:
            if i.get("name") == task_id:
                i["status"] = 1
                break

        with open(file = "index.json", mode = "w", encoding = "utf-8") as f:
            json.dump(data, f, indent = 4, ensure_ascii = False)

        se, mi, ho, da, we, mo = i.get('cron').split()
        scheduler.add_job(
            importlib.import_module(f"tasks.{i.get('task')}").main,
            trigger = CronTrigger(second=se, minute=mi, hour=ho, day=da, day_of_week=we, month=mo),
            id      = i.get('name'),
            args    = i.get('args', []),
            kwargs  = i.get('kwargs', {})
        )

        return responses.JSONResponse(
            status_code = 200,
            content = {
                    "detail": {
                    "status": "success",
                    "message": f"Task added",
                    "task_id": task_id,
                    "created": True
                }                   
            }
        )

@api.get("/task/") # Retorna os detalhes de todas as tarefas disponíveis
@api.get("/task/{task_id}") # Retorna os detalhes da tarefa especificada.
async def read(task_id: Optional[str] = None):
    with open(file = "index.json", mode = "r", encoding = "utf-8") as f:
        data = json.load(f)

    if task_id:
        for i in data:
            if i.get("name") == task_id:
                return responses.JSONResponse(
                    status_code = 200,
                    content = {
                        "status": "success",
                        "message": "Task details retrieved",
                        "task": i
                    }
                )

        return responses.JSONResponse(
            status_code = 404,
            content = {
                "status": "failure",
                "message": "Task not found",
                "task_id": task_id
            }
        )

    return responses.JSONResponse(
        status_code = 200,
        content = {
            "status": "success",
            "message": "List of all tasks",
            "tasks": data
        }
    )

@api.post("/task/") # Registra uma nova tarefa
async def create(task: TaskModel):
    with open(file = "index.json", mode = "r", encoding = "utf-8") as f:
        data = json.load(f)

    if task.name in [i.get("name") for i in data]:
        return HTTPException(
            status_code = 400,
            detail = {
                "status": "failure",
                "message": "Task id already exists",
                "task_id": task.name,
                "created": False
            }
        )

    if task.task not in os.listdir("tasks"):
        return HTTPException(
            status_code = 400,
            detail = {
                "status": "failure",
                "message": "Task not found",
                "task_id": task.task,
                "created": False
            }
        )
    
    if task.cron.split() != 6:
        return HTTPException(
            status_code = 400,
            detail = {
                "status": "failure",
                "message": "Invalid cron format",
                "task_id": task.cron,
                "created": False
            }
        )

    data.append(task.model_dump())

    with open(file = "index.json", mode = "w", encoding = "utf-8") as f:
        json.dump(data, f, indent = 4, ensure_ascii = False)

    return responses.JSONResponse(
        status_code = 200,
        content = {
            "status": "success",
            "message": "Task created",
            "task": task.model_dump(),
            "created": True
        }
    )

@api.delete("/task/") # Desativa uma tarefa, mas não remove
async def deactive(task_id: str):
    with open("index.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)

    for i in data:
        if task_id == i.get("name"):
            if i.get("status") == 0:
                return responses.JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Task is already disabled",
                        "task_id": task_id,
                        "disabled": False
                    }
                )
            else:
                i["status"] = 0
                with open("index.json", mode="w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                return responses.JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Task disabled",
                        "task_id": task_id,
                        "disabled": True
                    }
                )

    # Caso a tarefa não seja encontrada
    raise HTTPException(
        status_code=400,
        detail={
            "status": "failure",
            "message": "Task not found",
            "task_id": task_id,
            "disabled": False
        }
    )

@api.patch("/task/") # Ativa uma tarefa, mas não remove
async def deactive(task_id: str):
    with open("index.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)

    for i in data:
        if task_id == i.get("name"):
            if i.get("status") == 1:
                return responses.JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Task is already enabled",
                        "task_id": task_id,
                        "enabled": False
                    }
                )
            else:
                i["status"] = 1
                with open("index.json", mode="w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                return responses.JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Task enabled",
                        "task_id": task_id,
                        "enabled": True
                    }
                )

    # Caso a tarefa não seja encontrada
    raise HTTPException(
        status_code=400,
        detail={
            "status": "failure",
            "message": "Task not found",
            "task_id": task_id,
            "enabled": False
        }
    )