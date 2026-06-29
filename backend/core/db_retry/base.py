import time
import logging
from django.db.backends.postgresql.base import DatabaseWrapper as PgDatabaseWrapper

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2


class DatabaseWrapper(PgDatabaseWrapper):
    def get_new_connection(self, conn_params):
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return super().get_new_connection(conn_params)
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "DB connection attempt %d/%d failed: %s — retrying in %ds",
                        attempt, MAX_RETRIES, e, RETRY_DELAY,
                    )
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("DB connection failed after %d attempts", MAX_RETRIES)
        raise last_err
