class FileNotFoundError(OSError):
    """Base class for lookup errors."""

    def __init__(self, file_path):  # real signature unknown
        super(FileNotFoundError, self).__init__(str(file_path) + " missing")
        self._file_path = file_path

    @property
    def file_path(self):
        return self._file_path


class FilesNotFoundError(OSError):
    """Base class for multi-file lookup errors."""

    def __init__(self, file_paths):  # real signature unknown
        file_path_strs = [
            str(file_path) for file_path in file_paths if file_path is not None
        ]
        super(FilesNotFoundError, self).__init__(
            ", ".join(file_path_strs) + " are missing"
        )
        self._file_paths = [
            file_path for file_path in file_paths if file_path is not None
        ]

    @property
    def file_paths(self):
        return [file_path for file_path in self._file_paths]
