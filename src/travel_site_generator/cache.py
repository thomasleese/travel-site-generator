import logging
import platformdirs
import sqlite3


logger = logging.getLogger(__name__)
base_path = platformdirs.user_cache_path("travel-site-generator")


class SQLiteCache:
    def __init__(self, *, name: str):
        path = base_path / f"{name}.db"
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Loading from %s", path)

        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

        self.set_up_tables()

    def set_up_tables(self):
        raise NotImplementedError
