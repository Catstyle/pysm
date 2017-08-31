def _nop(state, event):
    return True


def on_event(name):
    def wrapper(func):
        func.on_event = name
        return func
    return wrapper
