import logging
from time import time
import os
from logging import handlers

file_max_bytes = 10 * 1024 * 1024
class LoggingHelper(object):
    INSTANCE = None

    def __init__(self, config):
        if LoggingHelper.INSTANCE is not None:
            raise ValueError("An instantiation already exists!")

        os.makedirs(config.Logger_Path, exist_ok=True)
        self.logger = logging.getLogger()

        logging.basicConfig(filename='LOGGER', level=logging.INFO)

        # fileHandler = logging.FileHandler(config.Logger_Path + '/msg.log')
        fileHandler = handlers.RotatingFileHandler(filename=config.Logger_Path + '/msg.log', maxBytes=file_max_bytes, backupCount=10)
        streamHandler = logging.StreamHandler()

        fomatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
        fileHandler.setFormatter(fomatter)
        streamHandler.setFormatter(fomatter)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(streamHandler)

    @classmethod
    def get_instace(cls, config):
        if cls.INSTANCE is None:
            cls.INSTANCE = LoggingHelper(config)
        return cls.INSTANCE

    @staticmethod
    def diff_time_logger(messege, start_time, config):
        LoggingHelper.get_instace(config).logger.info("[{}] :: running time {}".format(messege, time() - start_time))


