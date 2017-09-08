from unittest import TestCase

from pysm.utils import on_event, get_event_handlers


class Stuff(object):

    @on_event('off_duty')
    def off_duty(self):
        pass


class TestUtils(TestCase):

    def test_on_event(self):
        stuff = Stuff()
        self.assertEqual(stuff.off_duty.on_event, 'off_duty')

    def test_get_event_handlers(self):
        stuff = Stuff()
        self.assertDictEqual(
            get_event_handlers(stuff), {'off_duty': stuff.off_duty}
        )
