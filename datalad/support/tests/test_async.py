# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""(comparable) descriptors of the file status

"""

__docformat__ = 'restructuredtext'

from ..async import async
from datalad.tests.utils import eq_

# multiprocessing -- so returned would stay
# unmonified
returned = []


@async
def delay(uid):
    import time
    time.sleep(abs(2-uid)*0.01)
    returned.append(uid)
    return uid


def delay_sync(uid):
    import time
    #print("starting for %d" % uid)
    time.sleep(abs(2-uid)*0.01)
    #print("finishing for %d" % uid)
    return uid


def test_delay(delay=delay):
    results_async = list(map(delay, range(4)))
    results = [r.get() for r in results_async]
    eq_(returned, [])  # multiprocessing -- unmodified
    eq_(results, list(range(4)))


def test_delay_sync():
    # so we can still decorate function at run time within
    # a function
    delay_async = async(delay_sync)
    test_delay(delay=delay_async)