"""

    Zope 2 style module init

"""

# W0613:  7,15:initialize: Unused argument 'context'
# pylint: disable=W0613

# Run in monkey-patch
from silvuple import negotiator


def initialize(context):
    """ Zope 2 init code goes here.

    Usually there is nothing to go here,
    so move foward.
    """
