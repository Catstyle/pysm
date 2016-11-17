import inspect
import re
from functools import partial
from copy import deepcopy

from .state import State, WhateverState
from .event import Event, InstanceEvent
from .error import InvalidEventState


sub1 = re.compile(r'([A-Z]+)([A-Z][a-z])')
sub2 = re.compile(r'([a-z\d])([A-Z])')


def underscore(name):
    name = sub1.sub(r'\1_\2', name)
    name = sub2.sub(r'\1_\2', name)
    return name.replace('-', '_').lower()


def validate_state(clz, state_name):
    state = clz._pysm_states.get(state_name)
    if not inspect.isclass(state) or not issubclass(state, State):
        raise InvalidEventState(
            '%s, %s is not inherit from `State`' % (state_name, state)
        )


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
    from_state = instance.current_state
    instance.current_state = None
    return from_state


def switch_state(instance, to_state, *args, **kwargs):
    instance.exit_state(to_state)
    from_state = detach_state(instance)
    instance._pysm_previous_state = from_state
    attach_state(instance, to_state)
    instance.enter_state(from_state, *args, **kwargs)


def update_state(instance, *args, **kwargs):
    if not instance.can_switch_state():
        return
    current_name = instance.current_state.__name__
    for to_state, handler, hook in instance._pysm_rules.get(current_name, []):
        if handler is True:
            result = True
        else:
            assert isinstance(handler, str)
            if handler.startswith('!'):
                result = not getattr(instance, handler[1:])()
            else:
                result = getattr(instance, handler)()
        if result:
            hook = getattr(instance, hook, None)
            if hook:
                hook()
            event_name = 'switch_to_%s' % underscore(to_state)
            getattr(instance, event_name)(*args, **kwargs)
            break
    else:
        assert False, ('should have switched', instance._pysm_rules)


def add_state(obj, state, force=False):
    if not getattr(obj, 'initiated_pysm', False):
        raise TypeError('object is not a valid pysm state machine')
    if not (inspect.isclass(state) and issubclass(state, State)):
        raise ValueError('state is not a valid State')

    state_name = state.__name__
    if state_name in obj.__dict__ and not force:
        raise TypeError('obj already has state: %s' % state_name)
    obj._pysm_states[state_name] = state
    setattr(obj, state_name, state)


def add_event(obj, state_name, event):
    validate_state(obj, state_name)
    event_name = 'switch_to_%s' % underscore(state_name)
    assert event_name not in obj._pysm_events, (event_name, obj._pysm_events)
    event.name = event_name
    obj._pysm_events[event_name] = event
    setattr(obj, event_name, event)


def add_switch_rule(obj, from_state, to_state, handler, hook='', first=False):
    if not getattr(obj, 'initiated_pysm', False):
        raise TypeError('instance object is not a valid pysm state machine')
    rules = obj._pysm_rules
    try:
        if first:
            rules[from_state].insert(0, (to_state, handler, hook))
        else:
            rules[from_state].append((to_state, handler, hook))
    except KeyError:
        rules[from_state] = [(to_state, handler, hook)]


def add_instance_state(instance, state):
    if inspect.isclass(instance):
        raise ValueError('cannot add state to non instance object, '
                         'check class.add_pysm_state instead')
    if '_pysm_states' not in instance.__dict__:
        instance.__dict__['_pysm_states'] = instance._pysm_states.copy()
    add_state(instance, state, False)
    add_instance_event(instance, state.__name__)


def add_class_state(clz, state, force=False):
    if not inspect.isclass(clz):
        raise ValueError('cannot add state to non class object, '
                         'check instance.add_pysm_state instead')
    add_state(clz, state, force)
    add_class_event(clz, state.__name__)


def add_instance_event(instance, state_name):
    if '_pysm_events' not in instance.__dict__:
        instance.__dict__['_pysm_events'] = instance._pysm_events.copy()
    add_event(instance, state_name, InstanceEvent(instance, state_name))


def add_class_event(clz, state_name):
    add_event(clz, state_name, Event(state_name))


def add_instance_switch_rule(instance, from_state, to_state, handler, hook='',
                             first=False):
    if inspect.isclass(instance):
        raise ValueError('cannot add switch rule to non instance object, '
                         'check class.add_pysm_switch_rule instead')
    if '_pysm_rules' not in instance.__dict__:
        instance.__dict__['_pysm_rules'] = deepcopy(instance._pysm_rules)
    add_switch_rule(instance, from_state, to_state, handler, hook, first)


def add_class_switch_rule(clz, from_state, to_state, handler, hook=''):
    if not inspect.isclass(clz):
        raise ValueError('cannot add state to non class object, '
                         'check instance.add_pysm_state instead')
    add_switch_rule(clz, from_state, to_state, handler, hook)


def process_states(clz):
    clz._pysm_initial_state = None
    for name, state in inspect.getmembers(clz):
        if not (inspect.isclass(state) and issubclass(state, State)):
            continue
        if issubclass(state, WhateverState):
            raise TypeError('cannot inherit from WhateverState')

        clz._pysm_states[name] = state
        add_class_event(clz, name)

        if getattr(state, 'initial', False):
            if clz._pysm_initial_state is not None:
                raise ValueError("multiple initial states!")
            clz._pysm_initial_state = state

    if clz._pysm_initial_state is None:
        raise ValueError('missing initial state')


def process_rules(clz):
    clz._pysm_rules = {}

    switch_rules = getattr(clz, 'pysm_switch_rules', {})
    for from_state, rules in switch_rules.items():
        for rule in rules:
            add_class_switch_rule(clz, from_state, *rule)


def init_pysm(instance):
    instance._pysm_state_methods = set()
    instance._pysm_previous_state = None
    instance.current_state = None
    instance.__dict__['update_state'] = partial(update_state, instance)
    instance.__dict__['add_pysm_switch_rule'] = partial(
        add_instance_switch_rule, instance
    )
    instance.__dict__['add_pysm_state'] = partial(add_instance_state, instance)
    attach_state(instance, instance._pysm_initial_state)


def state_machine(original_class):
    original_class.initiated_pysm = True
    original_class.add_pysm_switch_rule = partial(
        add_class_switch_rule, original_class
    )
    original_class.add_pysm_state = partial(add_class_state, original_class)
    original_class._pysm_states = {'WhateverState': WhateverState}
    original_class._pysm_events = {}

    process_states(original_class)
    process_rules(original_class)

    original_init = original_class.__init__

    def new_init(self, *args, **kwargs):
        init_pysm(self)
        original_init(self, *args, **kwargs)
    original_class.__init__ = new_init
    return original_class
