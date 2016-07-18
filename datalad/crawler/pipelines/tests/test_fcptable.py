# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from ....support.annexrepo import AnnexRepo

from ....utils import chpwd
from ....utils import swallow_logs
from ....tests.utils import eq_, assert_not_equal, ok_, assert_raises
from ....tests.utils import with_tempfile
from datalad.crawler.pipelines.tests.utils import _test_smoke_pipelines
import logging
from logging import getLogger
lgr = getLogger('datalad.crawl.tests')

from ..fcptable import pipeline, superdataset_pipeline


def test_smoke_pipelines():
    yield _test_smoke_pipelines, pipeline, 'bogus'
    yield _test_smoke_pipelines, superdataset_pipeline, None
