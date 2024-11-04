from core.models.task import Task

# Função para criar uma nova Task
async def create_task(name: str, description: str, active: bool = True) -> Task:
    task = await Task.create(name=name, description=description, active=active)
    return task

# Função para obter uma Task pelo ID
async def get_task(task_id: int) -> Task:
    task = await Task.get(id=task_id)
    return task

# Função para atualizar uma Task pelo ID
async def update_task(task_id: int, name: str = None, description: str = None, active: bool = None) -> Task:
    task = await Task.get(id=task_id)
    if name is not None:
        task.name = name
    if description is not None:
        task.description = description
    if active is not None:
        task.active = active
    await task.save()  # Salva as alterações
    return task

# Função para deletar uma Task pelo ID
async def delete_task(task_id: int) -> None:
    task = await Task.get(id=task_id)
    await task.delete()  # Deleta a Task do banco de dados