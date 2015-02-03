pysm
==============

state machine for humans

There are two types of developers in this world: those who love state
machines and those who *will* eventually.

I fall in the first camp. I think it is really important to have a
declarative way to define the states of an object. That’s why I
developed ``pysm``.

Install
-------

.. code:: bash

    pip install pysm

Basic Usage
-----------

.. code:: python
    import pysm


    @pysm.state_machine
    class Person():
        name = 'Billy'

        sleeping = State(initial=True)
        running = State()
        cleaning = State()

        run = Event(from_states=sleeping, to_state=running)
        cleanup = Event(from_states=running, to_state=cleaning)
        sleep = Event(from_states=(running, cleaning), to_state=sleeping)

        @before('sleep')
        def do_one_thing(self):
            print "{} is sleepy".format(self.name)

        @before('sleep')
        def do_another_thing(self):
            print "{} is REALLY sleepy".format(self.name)

        @after('sleep')
        def snore(self):
            print "Zzzzzzzzzzzz"

        @after('sleep')
        def big_snore(self):
            print "Zzzzzzzzzzzzzzzzzzzzzz"

    person = Person()
    print person.current_state == Person.sleeping       # True
    print person.is_sleeping                            # True
    print person.is_running                             # False
    person.run()
    print person.is_running                             # True
    person.sleep()

    # Billy is sleepy
    # Billy is REALLY sleepy
    # Zzzzzzzzzzzz
    # Zzzzzzzzzzzzzzzzzzzzzz

    print person.is_sleeping                            # True

Features
--------

Before / After Callback Decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add callback hooks that get executed before or after an event
(see example above).

*Important:* if the *before* event causes an exception or returns
``False``, the state will not change (transition is blocked) and the
*after* event will not be executed.

Blocks invalid state transitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An *InvalidStateTransition Exception* will be thrown if you try to move
into an invalid state.

ORM support
-----------

We have basic support for `mongoengine`_, and `sqlalchemy`_.

Mongoengine
~~~~~~~~~~~

Just have your object inherit from ``mongoengine.Document`` and
state\_machine will add a StringField for state.

*Note:* You must explicitly call #save to persist the document to the
datastore.

.. code:: python

        @pysm.state_machine
        class Person(mongoengine.Document):

            name = mongoengine.StringField(default='Billy')

            class Sleeping(pysm.State):

                initial = True

                def enter(self, from_state):
                    pass

                def exit(self, to_state):
                    pass

            class Running(pysm.State):

                def enter(self, from_state):
                    pass

                def exit(self, to_state):
                    pass

            class Cleaning(pysm.State):

                def enter(self, from_state):
                    pass

                def exit(self, to_state):
                    pass

            run = Event(from_states=Sleeping, to_state=Running)
            cleanup = Event(from_states=Running, to_state=Cleaning)
            sleep = Event(from_states=(Running, Cleaning), to_state=Sleeping)


        person = Person()
        person.save()
        eq_(person.current_state, Person.Sleeping)
        assert person.is_sleeping
        assert not person.is_running
        person.run()
        assert person.is_running
        person.sleep()
        assert person.is_sleeping
        person.run()
        person.save()

.. _mongoengine: http://mongoengine.org/
.. _sqlalchemy: http://www.sqlalchemy.org/

Sqlalchemy
~~~~~~~~~~

All you need to do is have sqlalchemy manage your object. For example:

.. code:: python

        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
        @pysm.state_machine
        class Puppy(Base):
           ...


Thank you
---------

to `aasm`_ and ruby’s `state\_machine`_ and all other state machines
that I loved before

.. _aasm: https://github.com/aasm/aasm
.. _state\_machine: https://github.com/pluginaweek/state_machine
.. _state\_machine: https://github.com/jtushman/state_machine

