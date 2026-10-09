# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Shell completion of parameter values

A :class:`~datalad.support.param.Parameter` declares how its values are to be
completed via its ``completer``: either the name of one of the `completers`
below, or a callable following the argcomplete completer protocol, i.e.
accepting ``prefix``, ``action``, ``parser``, and ``parsed_args`` keyword
arguments and returning an iterable of candidate values.  The CLI parser
attaches it to the respective ``argparse`` action, but only when invoked
by argcomplete.

This module is only imported for shell completion, which runs on every <TAB>
press, so it must stay fast to import.
"""

__docformat__ = 'restructuredtext'

import logging
import os

lgr = logging.getLogger('datalad.cli.completers')


def _get_dataset(parsed_args):
    """Return the dataset a command would operate on

    Honors any ``-C`` and ``-d/--dataset`` already given on the command line
    preceding the word to be completed.

    Raises
    ------
    NoDatasetFound
    """
    from datalad.distribution.dataset import require_dataset
    from datalad.utils import (
        chpwd,
        getpwd,
    )

    # -C is only acted upon after argument parsing, i.e. not yet when
    # completing, but -d must be interpreted relative to it
    path = getpwd()
    for p in getattr(parsed_args, 'change_path', None) or []:
        path = os.path.join(path, p)
    with chpwd(path):
        return require_dataset(
            getattr(parsed_args, 'dataset', None),
            check_installed=True,
            purpose='shell completion')


def complete_siblings(prefix, parsed_args, **kwargs):
    """Names of the siblings of the dataset a command would operate on"""
    from datalad.support.exceptions import (
        CapturedException,
        NoDatasetFound,
    )
    try:
        ds = _get_dataset(parsed_args)
    except NoDatasetFound as e:
        lgr.debug("No sibling names to complete: %s", CapturedException(e))
        return []
    return sorted(r for r in ds.repo.get_remotes() if r.startswith(prefix))


completers = {
    'siblings': complete_siblings,
}


def get_completer(spec):
    """Resolve a `Parameter.completer` specification

    Parameters
    ----------
    spec: str or callable
      Name of a known completer, or a completer callable that is returned
      as is.

    Returns
    -------
    callable or None
      None for an unknown completer name, to fall back on the default
      completion.
    """
    if callable(spec):
        return spec
    completer = completers.get(spec)
    if completer is None:
        lgr.warning("Unknown completer %r, known are: %s",
                    spec, ', '.join(completers))
    return completer
