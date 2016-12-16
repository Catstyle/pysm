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
    assert instance.current_state is None, instance.current_state
    base_dict = instance.__dict__
    for name, method in state.state_methods.items():
        base_dict[name] = partial(method, instance)
        instance._pysm_state_methods.add(name)
    instance.current_state = state


def detach_state(instance):
    assert instance.current_state, instance.current_state
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
    rules = instance._pysm_rules.get(instance.current_state.__name__, [])
    for to_state, prerequisites, negative, hook in rules:
        if prerequisites is not True:
            assert isinstance(prerequisites, list)
            target = instance
            for prerequisite in prerequisites:
                target = getattr(target, prerequisite)
            if callable(target):
                target = target()
            prerequisite = not target if negative else target
        else:
            prerequisite = True
        if prerequisite:
            hook = getattr(instance, hook, None)
            if hook:
                hook()
            event_name = 'switch_to_%s' % underscore(to_state)
            getattr(instance, event_name)(*args, **kwargs)
            break
    else:
        assert False, (instance.current_state, rules, instance._pysm_rules)


def add_state(obj, state_name, state, force=False):
    if not getattr(obj, 'initiated_pysm', False):
        raise TypeError('`%s` is not a valid pysm state machine' % obj)
    if not (inspect.isclass(state) and issubclass(state, State)):
        raise TypeError('state is not a valid State')

    if state_name in obj.__dict__ and not force:
        raise ValueError('`%s` already has state: %s' % (obj, state_name))
    if '_pysm_states' not in obj.__dict__:
        if inspect.isclass(obj):
            setattr(obj, '_pysm_states', obj._pysm_states.copy())
        else:
            obj.__dict__['_pysm_states'] = obj._pysm_states.copy()
    obj._pysm_states[state_name] = state
    setattr(obj, state_name, state)


def add_states(obj, states):
    for state in states:
        add_class_state(obj, state.__name__, state, True)
        if getattr(state, 'initial', False):
            if obj._pysm_initial_state is not None:
                raise ValueError("multiple initial states!")
            obj._pysm_initial_state = state


def add_event(obj, state_name, event, force=False):
    validate_state(obj, state_name)
    event_name = 'switch_to_%s' % underscore(state_name)
    if event_name in obj._pysm_events and not force:
        raise ValueError('`%s` already has event: %s' % (obj, event_name))
    if '_pysm_events' not in obj.__dict__:
        if inspect.isclass(obj):
            setattr(obj, '_pysm_events', obj._pysm_events.copy())
        else:
            obj.__dict__['_pysm_events'] = obj._pysm_events.copy()
    event.name = event_name
    obj._pysm_events[event_name] = event
    setattr(obj, event_name, event)


def add_switch_rule(obj, from_state, to_state, prerequisite, hook='',
                    first=False):
    if not getattr(obj, 'initiated_pysm', False):
        raise TypeError('`%s` is not a valid pysm state machine' % obj)
    rules = obj._pysm_rules
    if prerequisite is True:
        prerequisites, negative = True, False
    elif prerequisite.startswith('!'):
        prerequisites, negative = prerequisite[1:].split('.'), True
    else:
        prerequisites, negative = prerequisite.split('.'), False
    try:
        if first:
            rules[from_state].insert(
                0, (to_state, prerequisites, negative, hook)
            )
        else:
            rules[from_state].append((to_state, prerequisites, negative, hook))
    except KeyError:
        rules[from_state] = [(to_state, prerequisites, negative, hook)]


def add_switch_rules(obj, switch_rules):
    for from_state, rules in switch_rules.items():
        for rule in rules:
            add_switch_rule(obj, from_state, *rule)


def add_instance_state(instance, state_name, state, force=False):
    if inspect.isclass(instance):
        raise TypeError('cannot add state to non instance object, '
                        'check class.add_pysm_state instead')
    add_state(instance, state_name, state, force)
    add_instance_event(instance, state_name, force)


def add_class_state(clz, state_name, state, force=False):
    if not inspect.isclass(clz):
        raise TypeError('cannot add state to non class object, '
                        'check instance.add_pysm_state instead')
    add_state(clz, state_name, state, force)
    add_class_event(clz, state_name, force)


def add_instance_event(instance, state_name, force=False):
    add_event(instance, state_name, InstanceEvent(instance, state_name), force)


def add_class_event(clz, state_name, force=False):
    add_event(clz, state_name, Event(state_name), force)


def add_instance_switch_rule(instance, from_state, to_state, prerequisite,
                             hook='', first=False):
    if inspect.isclass(instance):
        raise TypeError('cannot add switch rule to non instance object, '
                        'check class.add_pysm_switch_rule instead')
    if '_pysm_rules' not in instance.__dict__:
        instance.__dict__['_pysm_rules'] = deepcopy(instance._pysm_rules)
    add_switch_rule(instance, from_state, to_state, prerequisite, hook, first)


def add_class_switch_rule(clz, from_state, to_state, prerequisite, hook=''):
    if not inspect.isclass(clz):
        raise TypeError('cannot add state to non class object, '
                        'check instance.add_pysm_state instead')
    add_switch_rule(clz, from_state, to_state, prerequisite, hook)


def init_pysm(ins):
    ins._pysm_state_methods = set()
    ins._pysm_previous_state = None
    ins.current_state = None
    ins.__dict__['update_state'] = partial(update_state, ins)

    if ins._pysm_initial_state is None:
        raise ValueError('missing initial state')
    attach_state(ins, ins._pysm_initial_state)


def state_machine(clz):
    clz.initiated_pysm = True

    clz._pysm_states = {'WhateverState': WhateverState}
    clz._pysm_events = {}
    clz._pysm_initial_state = None
    clz._pysm_rules = {}

    states = []
    for name, state in inspect.getmembers(clz):
        if not (inspect.isclass(state) and issubclass(state, State)):
            continue
        if issubclass(state, WhateverState):
            raise TypeError('cannot inherit from WhateverState')
        states.append(state)

    add_states(clz, states)
    add_switch_rules(clz, getattr(clz, 'pysm_switch_rules', {}))

    original_init = clz.__init__

    def new_init(self, *args, **kwargs):
        init_pysm(self)
        original_init(self, *args, **kwargs)
    clz.__init__ = new_init
    return clz
