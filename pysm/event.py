from .error import InvalidTransition, HasNoState


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
            current_name = current_state.__name__
            if current_name not in self.from_states:
                raise InvalidTransition(
                    '%s: calling `%s` from state `%s`, valid states `%s`' % (
                        instance, self.name, current_name, self.from_states
                    )
                )
            to_state = instance._pysm_states.get(self.to_state)
            if not to_state:
                raise HasNoState(self.to_state)
            switch_state(instance, current_state, to_state, *args, **kwargs)
        return switch

    def __str__(self):
        return u'pysm-event|%s' % self.name
    __unicode__ = __repr__ = __str__


class RestoreEvent(Event):

    def __get__(self, instance, owner):
        if not instance:
            return self
        restore_event = getattr(instance, 'restore_from_' + self.name)
        restore_event.to_state = instance.current_state.__name__
        return super(RestoreEvent, self).__get__(instance, owner)

    def __str__(self):
        return u'pysm-restoreevent|%s' % self.name
    __unicode__ = __repr__ = __str__


from .handler import switch_state  # noqa
