def on_event(name):
    def wrapper(func):
        func.on_event = name
        return func
    return wrapper


def get_event_handlers(obj):
    handlers = {}
    for attr in dir(obj):
        if attr.startswith('__'):
            continue
        value = getattr(obj, attr)
        if getattr(value, 'on_event', ''):
            handlers[value.on_event] = value
    return handlers
