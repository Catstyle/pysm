from __future__ import absolute_import

try:
    import mongoengine
except ImportError as e:
    mongoengine = None

from pysm.orm.base import BaseAdaptor


class MongoAdaptor(BaseAdaptor):

    def get_class_members(self, original_class):
        # reimplementing inspect.getmembers to swallow ConnectionError
        results = []
        for key in dir(original_class):
            try:
                value = getattr(original_class, key)
            except (AttributeError, mongoengine.ConnectionError):
                continue
            results.append((key, value))
        results.sort()
        return results

    def extra_class_members(self, initial_state):
        return {'state_name': mongoengine.StringField(default=initial_state.name)}

    @classmethod
    def update(cls, instance, state_name):
        instance.state_name = state_name


def get_mongo_adaptor(original_class):
    if mongoengine and issubclass(original_class, mongoengine.Document):
        return MongoAdaptor
    return None
