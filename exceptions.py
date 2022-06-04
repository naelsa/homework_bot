class EmptyAPIAnswer(Exception):
    """Кастомное исключение при пустом ответе API."""

    pass


class APIAnswerError(Exception):
    """Кастомное исключение при незапланированной работе API."""

    pass


class SendMessageException(Exception):
    """Кастомное исключение при ошибке отправки сообщения."""

    pass


class ConnectionError(Exception):
    """Кастомное исключение при невозможности получения ответа."""

    pass
