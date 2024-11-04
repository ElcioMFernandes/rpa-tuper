import sys
import core.settings
import core.models
from tortoise import Tortoise, run_async

async def init():
    await Tortoise.init(
        db_url=core.settings.DATABASE_URL,
        modules={"models": ["core.models"]}
    )
    await Tortoise.generate_schemas()
    print("Database and tables created!")

# Run the init function to create the database and tables
if sys.argv[1] == 'migrate':
    run_async(init())
