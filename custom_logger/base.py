import logging
from abc import ABC, abstractmethod
from enum import Enum


class AbstractLogger(ABC):
    @abstractmethod
    def debug(self, message: str):
        ...

    @abstractmethod
    def info(self, message: str):
        ...

    @abstractmethod
    def warning(self, message: str):
        ...

    @abstractmethod
    def error(self, message: str):
        ...

    @abstractmethod
    def critical(self, message: str):
        ...


class BaseLogger(AbstractLogger):
    def __init__(self, name: str = "uvicorn", level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.setLevel(level)
        stream_output = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_output.setFormatter(formatter)
        self.logger.addHandler(stream_output)
        self.logger.propagate = False

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)


class LoggerType(Enum):
    default = "base_logger"


def get_logger(logger_type: LoggerType, **kwargs) -> AbstractLogger:
    if logger_type == LoggerType.default:
        return BaseLogger(**kwargs)

    raise ValueError(f"Unsupported logger type: {logger_type}")
