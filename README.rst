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

        class Sleeping(pysm.State):

            initial = True

            def enter_state(self, from_state):
                print 'enter state Sleeping from %s' % (Sleeping, from_state)

            def exit_state(self, to_state):
                print 'exit state Sleeping to %s' % (Sleeping, to_state)

        class Running(pysm.State):

            def enter_state(self, from_state):
                print 'enter state Running from %s' % (Running, from_state)

            def exit_state(self, to_state):
                print 'exit state Running to %s' % (Running, to_state)

        class Cleaning(pysm.State):

            def enter_state(self, from_state):
                print 'enter state Cleaning from %s' % (Cleaning, from_state)

            def exit_state(self, to_state):
                print 'exit state Cleaning to %s' % (Cleaning, to_state)

        run = Event(from_states=Sleeping, to_state=Running)
        cleanup = Event(from_states=Running, to_state=Cleaning)
        sleep = Event(from_states=(Running, Cleaning), to_state=Sleeping)


    person = Person()
    print person.current_state == Person.Sleeping       # True
    print person.is_sleeping                            # True
    print person.is_running                             # False
    person.run()
    print person.is_running                             # True
    person.sleep()

    # exit state Sleeping to Running
    # enter state Running from Sleeping
    # exit state Running to Sleeping 
    # enter state Sleeping from Running

    print person.is_sleeping                            # True

Features
--------

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

                def enter_state(self, from_state):
                    pass

                def exit_state(self, to_state):
                    pass

            class Running(pysm.State):

                def enter_state(self, from_state):
                    pass

                def exit_state(self, to_state):
                    pass

            class Cleaning(pysm.State):

                def enter_state(self, from_state):
                    pass

                def exit_state(self, to_state):
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

to `aasm`_ and ruby’s `state\_machine`_ and jtushman's `jtushman/state\_machine`_ and
all other state machines that I loved before

.. _aasm: https://github.com/aasm/aasm
.. _state\_machine: https://github.com/pluginaweek/state_machine
.. _jtushman/state\_machine: https://github.com/jtushman/state_machine
