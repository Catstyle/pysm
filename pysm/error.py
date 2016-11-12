class PysmError(Exception):
    pass


class InvalidTransition(PysmError):
    pass


class InvalidEventState(PysmError):
    pass


class HasNoState(PysmError):
    pass
