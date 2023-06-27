import logging
import random

import sys
import time

logger = logging.getLogger(__name__)


def retry_with_backoff(
    retries: int = 3, backoff_in_secs: float = 1, fail_open=False, test_mode=False
):
    def fn(f):
        def wrapper(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    x = f(*args, **kwargs)
                    return x
                except:
                    logger.warning("failed execution", exc_info=sys.exc_info())
                    if attempt >= retries:
                        logger.info(f"max retries ({retries}) reached")
                        if not fail_open:
                            raise
                        return None

                    sleep = backoff_in_secs * 2 ** attempt + random.uniform(0, 1)
                    time.sleep(sleep) if not test_mode else None
                    attempt += 1

        return wrapper

    return fn
