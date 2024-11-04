from tortoise import fields
from tortoise.models import Model
from datetime import datetime

class Sched(Model):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250)
    active = fields.BooleanField(default=True)
    scheduler_type = fields.CharField(
        max_length=8, 
        choices=[("cron", "Cron"), ("interval", "Interval"), ("date", "Date")]
    )
    cron = fields.CharField(max_length=100, null=True)
    interval = fields.BigIntField(null=True)
    date = fields.DateField(null=True)
    created = fields.DatetimeField(default=datetime.utcnow)
    task = fields.ForeignKeyField("models.Task", related_name="scheds")
