from functools import partial


class InvalidTransition(Exception):
    pass


class Event(object):

    def __init__(self, from_states, to_state):
        if isinstance(from_states, (tuple, list)):
            self.from_states = tuple(from_states)
        else:
            self.from_states = (from_states,)
        self.to_state = to_state

    def __get__(self, instance, owner):
        if not instance:
            return self
        def switch(*args, **kwargs):
            current_state = instance.current_state
            if current_state not in self.from_states:
                raise InvalidTransition(
                    '%s: calling `%s` from state `%s`, valid states `%s`' % (
                        instance, self.name, current_state, self.from_states
                    )
                )
            switch_state(instance, current_state, self.to_state, *args, **kwargs)
        return switch

    def __str__(self):
        return u'pysm-event|%s' % self.name
    __unicode__ = __repr__ = __str__


class RestoreEvent(Event):

    def __get__(self, instance, owner):
        if not instance:
            return self
        restore_event = getattr(instance, 'restore_from_' + self.name)
        restore_event.to_state = instance.current_state
        return super(RestoreEvent, self).__get__(instance, owner)

    def __str__(self):
        return u'pysm-restoreevent|%s' % self.name
    __unicode__ = __repr__ = __str__


def attach_state(instance, state):
    assert instance.current_state is None
    base_dict = instance.__dict__
    for name, method in state.state_methods.items():
        base_dict[name] = partial(method, instance)
        instance._pysm_state_methods.add(name)
    instance.current_state = state


def detach_state(instance):
    assert instance.current_state
    base_dict = instance.__dict__
    for name in instance._pysm_state_methods:
        base_dict.pop(name, None)
    instance._pysm_state_methods.clear()
    instance.current_state = None


def switch_state(instance, from_state, to_state, *args, **kwargs):
    instance.exit_state(to_state)
    detach_state(instance)
    instance._pysm_previous_state = from_state
    attach_state(instance, to_state)
    instance.enter_state(from_state, *args, **kwargs)
