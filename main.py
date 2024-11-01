from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
import json, tasks, asyncio

with open('sched.json', 'r', -1, 'utf-8') as f:
    schedata = json.load(f)

async def run(task, args):
    if asyncio.iscoroutinefunction(getattr(tasks, task)):
        await getattr(tasks, task)(*args)
    else:
        getattr(tasks, task)(*args)

scheduler = AsyncIOScheduler(timezone=ZoneInfo("America/Sao_Paulo"))

for sched in schedata:
    if sched.get('task') in tasks.__all__ and sched.get('stat') == 'enabled':
        if len(sched.get('cron').split()) == 6:
            se, mi, ho, da, mo, do = sched.get('cron').split()
            trigger = CronTrigger(second=se, minute=mi, hour=ho, day=da, month=mo, day_of_week=do,timezone=ZoneInfo("America/Sao_Paulo"))
        scheduler.add_job(run, trigger, args=(sched.get('task'), sched.get('args')))

if __name__ == '__main__':
    scheduler.start()

try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()