from __future__ import absolute_import

from pysm.orm.base import NullAdaptor
from pysm.orm.mongoengine import get_mongo_adaptor
from pysm.orm.sqlalchemy import get_sqlalchemy_adaptor

_adaptors = [get_mongo_adaptor, get_sqlalchemy_adaptor]


def get_adaptor(original_class):
    # if none, then just keep state in memory
    for get_adaptor in _adaptors:
        adaptor = get_adaptor(original_class)
        if adaptor is not None:
            break
    else:
        adaptor = NullAdaptor
    return adaptor
