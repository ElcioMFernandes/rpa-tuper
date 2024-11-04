from datetime import datetime
from tortoise import fields
from tortoise.models import Model

class Task(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250)
    created = fields.DatetimeField(default=datetime.utcnow)
    scheds = fields.ReverseRelation["Sched"]

