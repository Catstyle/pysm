from __future__ import absolute_import
import inspect
import inflection

from pysm.models import Event, RestoreEvent, State, WhateverState, attach_state


def is_state_builder(state):
    def is_state(self):
        return self.current_state == state
    return property(is_state)


class BaseAdaptor(object):

    @classmethod
    def get_class_members(cls, original_class):
        return inspect.getmembers(original_class)

    @classmethod
    def process_states(cls, original_class):
        states, initial_state, is_method_dict = {}, None, {}
        for name, state in cls.get_class_members(original_class):
            if not (inspect.isclass(state) and issubclass(state, State)):
                continue

            states[name] = state
            if getattr(state, 'initial', False):
                if initial_state is not None:
                    raise ValueError("multiple initial states!")
                initial_state = state

            is_state_string = "is_" + inflection.underscore(name)
            is_method_dict[is_state_string] = is_state_builder(state)

        # placeholder state
        states[WhateverState.__name__] = WhateverState

        assert initial_state, 'missing initial state'
        return states, initial_state, is_method_dict

    @classmethod
    def process_events(cls, original_class, initial_state, states):
        original_class.initial_event = Event(
            from_states=(WhateverState), to_state=initial_state
        )
        for name, event in cls.get_class_members(original_class):
            if not isinstance(event, Event):
                continue
            event.name = name
            from_states = []
            for fs in event.from_states:
                from_states.append(states[fs.__name__])
            event.from_states = tuple(from_states)
            event.to_state = states[event.to_state.__name__]

            if isinstance(event, RestoreEvent):
                restore_name = 'restore_from_' + name
                restore_event = Event(
                    from_states=event.to_state,
                    to_state=states[WhateverState.__name__]
                )
                setattr(original_class, restore_name, restore_event)

    @classmethod
    def _process_class(cls, original_class):
        class_dict = {}

        # Get states
        states, initial_state, is_method_dict = cls.process_states(original_class)
        class_dict.update(is_method_dict)
        class_dict.update(cls.extra_class_members(initial_state))
        class_dict.update(states)

        # Get events
        cls.process_events(original_class, initial_state, states)

        original_init = original_class.__init__
        def new_init(self, *args, **kwargs):
            attach_state(self, WhateverState)
            self.initial_event()
            original_init(self, *args, **kwargs)
        class_dict['__init__'] = new_init
        class_dict['_origin_methods'] = {}
        class_dict['_state_methods'] = set()

        return class_dict

    @classmethod
    def process_class(cls, original_class):
        original_class._adaptor = cls
        class_dict = cls._process_class(original_class)
        for key, value in class_dict.items():
            setattr(original_class, key, value)
        return original_class

    @classmethod
    def extra_class_members(cls, initial_state):
        raise NotImplementedError

    @classmethod
    def update(cls, document, state_name):
        raise NotImplementedError


class NullAdaptor(BaseAdaptor):

    @classmethod
    def extra_class_members(cls, initial_state):
        return {}

    @classmethod
    def update(cls, instance, state_name):
        instance.state_name = state_name
