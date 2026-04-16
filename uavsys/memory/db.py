import aiosqlite
import os
from ..config import Config

class DatabaseManager:
    def __init__(self, config: Config):
        self.db_path = config.DB_PATH
        self.schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    async def init_db(self):
        """Initialize the database with schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            with open(self.schema_path, "r") as f:
                await db.executescript(f.read())
            await db.commit()

    def get_connection(self):
        """Get a connection context manager."""
        return aiosqlite.connect(self.db_path)
