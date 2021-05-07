class FileNotFoundError(AssertionError):
    """ Base class for lookup errors. """
    def __init__(self, file_path): # real signature unknown
        super(FileNotFoundError, self).__init__(str(file_path) + " missing")
        self._file_path = file_path

    @property
    def file_path(self):
        return self._file_path
