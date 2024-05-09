"""Модуль собственных исключений."""


class EnvironmentVariableException(Exception):
    """Класс исключения при отсутствии переменных среды."""

    def __init__(self, message):
        """Магический метод инициализации объектов."""
        super().__init__(message)


class WrongResponseCodeException(Exception):
    """Класс исключения, если код ответа не равен 200."""

    def __init__(self, message):
        """Магический метод инициализации объектов."""
        super().__init__(message)


class EmptyResponseException(Exception):
    """Класс исключения для пустого ответа API."""

    def __init__(self, message):
        """Магический метод инициализации объектов."""
        super().__init__(message)
