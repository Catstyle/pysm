from __future__ import absolute_import

try:
    import sqlalchemy
    from sqlalchemy.orm.instrumentation import ClassManager
except ImportError:
    sqlalchemy = None

from pysm.orm.base import BaseAdaptor


class SqlAlchemyAdaptor(BaseAdaptor):

    @classmethod
    def extra_class_members(cls, initial_state):
        return {'state_name': sqlalchemy.Column(sqlalchemy.String)}

    @classmethod
    def update(cls, instance, state_name):
        instance.state_name = state_name

    @classmethod
    def process_class(cls, original_class):
        class_dict = cls._process_class(original_class)
        for key, value in class_dict.items():
            setattr(original_class, key, value)
        return original_class


def get_sqlalchemy_adaptor(original_class):
    if (sqlalchemy and
            hasattr(original_class, '_sa_class_manager') and
            isinstance(original_class._sa_class_manager, ClassManager)):
        return SqlAlchemyAdaptor(original_class)
    return None
