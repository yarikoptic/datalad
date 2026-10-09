"""Tests for shell completion of parameter values"""

__docformat__ = 'restructuredtext'

import logging
from argparse import Namespace

from datalad.distribution.dataset import Dataset
from datalad.interface.base import (
    get_interface_groups,
    load_interface,
)
from datalad.tests.utils_pytest import (
    assert_equal,
    assert_in,
    assert_is,
    assert_is_none,
    with_tempfile,
)
from datalad.utils import swallow_logs

from ..completers import (
    complete_siblings,
    completers,
    get_completer,
)


@with_tempfile(mkdir=True)
def test_complete_siblings(path=None):
    ds = Dataset(path).create(annex=False)
    for name in ('origin', 'other'):
        ds.repo.add_remote(name, f'https://example.com/{name}')
    sub = ds.pathobj / 'sub'
    sub.mkdir()

    def complete(prefix='', **kwargs):
        return complete_siblings(prefix, parsed_args=Namespace(**kwargs))

    assert_equal(complete(dataset=path), ['origin', 'other'])
    assert_equal(complete('ot', dataset=path), ['other'])
    # -d is relative to -C, which could be given multiple times
    assert_equal(complete(change_path=[str(ds.pathobj.parent)],
                          dataset=ds.pathobj.name),
                 ['origin', 'other'])
    assert_equal(complete(change_path=[path, 'sub']), ['origin', 'other'])
    # no dataset, no completions
    assert_equal(complete(change_path=[path], dataset='nonexistent'), [])


def test_get_completer():
    assert_is(get_completer('siblings'), complete_siblings)

    def custom(prefix, **kwargs):
        return []

    assert_is(get_completer(custom), custom)
    with swallow_logs(new_level=logging.WARNING) as cml:
        assert_is_none(get_completer('bogus'))
        assert_in("Unknown completer 'bogus'", cml.out)


def test_known_completers():
    # all named completers of the core commands' parameters are known
    for _, _, specs in get_interface_groups():
        for spec in specs:
            for name, param in load_interface(spec)._params_.items():
                if isinstance(param.completer, str):
                    assert_in(param.completer, completers, msg=name)
