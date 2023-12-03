import logging

#TODO: Fix logger add more loggers

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

# handler = logging.FileHandler('logs_.txt')
# handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s %(message)s ')

# handler.setFormatter(formatter)

# logger.addHandler(handler)

logger.info("This is an info message")