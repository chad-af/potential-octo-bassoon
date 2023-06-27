from asyncio.log import logger


def _generate_message(message: str, **kwargs):
    params = [f"{k}: {str(v)}" for k, v in kwargs.items()]
    msg = f"{message} {', '.join(params)}"
    return msg


def log_info(message: str, **kwargs):
    logger.info(_generate_message(message, **kwargs))


def log_warning(message: str, **kwargs):
    logger.warning(_generate_message(message, **kwargs))
    # TODO: Log to sentry
    """
    if not dev: log to sentry
    """


def log_error(message: str, exc: Exception = None, **kwargs):
    logger.error(_generate_message(message, **kwargs))
    # TODO: Log to sentry
    """
    if not dev: log to sentry
    """
