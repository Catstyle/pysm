from __future__ import absolute_import
import inspect
import inflection

from pysm.models import Event, State


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
        states, initial_state, is_method_dict,  = {}, None, {}
        for name, state in cls.get_class_members(original_class):
            if not (inspect.isclass(state) and issubclass(state, State)):
                continue

            state_dict = {}
            state_name = state.__name__
            state_dict.update(original_class.__dict__)
            state_dict.update(state.__dict__)
            state = type(
                state_name,
                (State, original_class) + original_class.__bases__,
                state_dict
            )
            state.name = name

            states[state_name] = state
            if getattr(state, 'initial', False):
                if initial_state is not None:
                    raise ValueError("multiple initial states!")
                initial_state = state

            is_state_string = "is_" + inflection.underscore(name)
            is_method_dict[is_state_string] = is_state_builder(state)

        assert initial_state, 'missing initial state'
        return states, initial_state, is_method_dict

    @classmethod
    def process_events(cls, original_class, states):
        for name, event in cls.get_class_members(original_class):
            if not isinstance(event, Event):
                continue
            event.name = name
            from_states = []
            for fs in event.from_states:
                from_states.append(states[fs.__name__])
            event.from_states = tuple(from_states)
            event.to_state = states[event.to_state.__name__]

    @classmethod
    def _process_class(cls, original_class):
        class_dict = {}

        # Get states
        states, initial_state, is_method_dict = cls.process_states(original_class)
        class_dict.update(original_class.__dict__)
        class_dict.update(is_method_dict)
        class_dict.update(cls.extra_class_members(initial_state))
        class_dict.update(states)

        # Get events
        cls.process_events(original_class, states)

        def new_init(self, *args, **kwargs):
            original_class.__init__(self, *args, **kwargs)
            self.__class__ = self.current_state = initial_state
        class_dict['__init__'] = new_init

        return class_dict

    @classmethod
    def process_class(cls, original_class):
        original_class._adaptor = cls
        class_dict = cls._process_class(original_class)
        return type(original_class.__name__, original_class.__bases__, class_dict)

    @classmethod
    def extra_class_members(cls, initial_state):
        raise NotImplementedError

    @classmethod
    def update(cls, document, state_name):
        raise NotImplementedError
