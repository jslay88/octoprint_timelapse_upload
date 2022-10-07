from os import remove
from os.path import basename, isfile, join
from shutil import copyfile

from .base import BaseClient


class FileCopyClient(BaseClient):
    config = dict(
        local_path=dict(
            input_type="text",
            value=""
        )
    )
    display_name = "File Copy"

    def upload(self, path) -> bool:
        if not isfile(path):
            self._logger.warning(f'{path} is not a file! Cannot copy file!')
            return False
        copyfile(path, join(self._config["local_path"], basename(path)))
        return True
