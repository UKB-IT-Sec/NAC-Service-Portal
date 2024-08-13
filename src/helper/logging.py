import logging


def map_log_level_to_verbosity(verbosity):
    if verbosity == 0:
        return logging.ERROR
    if verbosity == 1:
        return logging.WARNING
    if verbosity == 2:
        return logging.INFO
    if verbosity == 3:
        return logging.DEBUG
    return logging.DEBUG


def setup_console_logger(verbosity):
    log_format = logging.Formatter(fmt='[%(asctime)s][%(module)s][%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger('')
    logger.setLevel(map_log_level_to_verbosity(verbosity))
    console_logger = logging.StreamHandler()
    console_logger.setFormatter(log_format)
    logger.addHandler(console_logger)
