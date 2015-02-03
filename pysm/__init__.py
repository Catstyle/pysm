from pysm.models import Event, State, Whatever
from pysm.orm import get_adaptor
from pysm.errors import InvalidStateTransition


def pysm(original_class):
    adaptor = get_adaptor(original_class)
    return adaptor.process_class(original_class)
