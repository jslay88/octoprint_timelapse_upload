import logging


class BaseClient(object):
    _logger = None
    config = None
    display_name = None

    def __init__(self, config):
        self._config = config
        self._logger = logging.getLogger(__name__)

    def upload(self, path) -> bool:
        raise NotImplementedError
