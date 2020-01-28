# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Benchmarks for DataLad"""

import os
import sys
import os.path as osp
from os.path import join as opj
import tarfile
import timeit

from time import time
from subprocess import call

try:
    from datalad.cmd import (
        WitlessRunner,
        kill_output,
        capture_output, lgr, linesep_bytes,
    )

    def witless_call(f):
        def func(*args):
            return f(*args).encode(), 0
        return func
    class Runner(WitlessRunner):
        def run(self, cmd, **kwargs):
            # shimming "renamed" kwargs
            # https://github.com/datalad/datalad/pull/4080/files#r371882230
            for out in 'stdout', 'stderr':
                proc_ = 'proc_' + out
                log_ = 'log_' + out
                v = kwargs.pop(log_, True)
                if not v:
                    pass
                elif v in ('offline', 'online', True):
                    # TODO: actually log
                    kwargs[proc_] = kill_output
                elif isinstance(v, (str, bytes)):
                    raise ValueError(v)
                else:
                    # callable -- we just pass all into it, and assume that
                    # nothing is left behind
                    # TODO: split on linesep_bytes and feed one line at a time?
                    kwargs[proc_] = witless_call(v)  # lambda x: (v(x), 0)
            kwargs.pop('log_online', None)  # it is implied (???)
            cmd_list = ["/bin/sh", "-c", cmd]
            return super(Runner, self).run(cmd_list, **kwargs)

except ImportError:
    from datalad.cmd import Runner

from datalad.api import add
from datalad.api import create
from datalad.api import create_test_dataset
from datalad.api import Dataset
from datalad.api import install
from datalad.api import ls
from datalad.api import remove
from datalad.api import uninstall

from datalad.utils import rmtree
from datalad.utils import getpwd

# Some tracking example -- may be we should track # of datasets.datalad.org
#import gc
#def track_num_objects():
#    return len(gc.get_objects())
#track_num_objects.unit = "objects"


from .common import SuprocBenchmarks

scripts_dir = osp.join(osp.dirname(__file__), 'scripts')
heavyout_cmd = "{} 1000".format(osp.join(scripts_dir, 'heavyout'))

class startup(SuprocBenchmarks):
    """
    Benchmarks for datalad commands startup
    """

    def setup(self):
        # we need to prepare/adjust PATH to point to installed datalad
        # We will base it on taking sys.executable
        python_path = osp.dirname(sys.executable)
        self.env = os.environ.copy()
        self.env['PATH'] = '%s:%s' % (python_path, self.env.get('PATH', ''))

    def time_help_np(self):
        call(["datalad", "--help-np"], env=self.env)
        
    def time_import(self):
        call([sys.executable, "-c", "import datalad"])

    def time_import_api(self):
        call([sys.executable, "-c", "import datalad.api"])


class runner(SuprocBenchmarks):
    """Some rudimentary tests to see if there is no major slowdowns from Runner
    """

    def setup(self):
        self.runner = Runner()
        # older versions might not have it
        try:
            from datalad.cmd import GitRunner
            self.git_runner = GitRunner()
        except ImportError:
            pass

    def time_echo(self):
        self.runner.run("echo")

    def time_echo_gitrunner(self):
        self.git_runner.run("echo")

    # Following "track" measures computing overhead comparing to the simplest
    # os.system call on the same command without carrying for in/out

    unit = "% overhead"

    def _get_overhead(self, cmd, nrepeats=10, **run_kwargs):
        """Estimate overhead over running command via the simplest os.system
        and to not care about any output.

        Returns % of overhead. So 0 - is no change. 100 -- twice slower.
        Cannot be below -100.
        """
        # asv does not repeat tracking ones I think, so nrepeats
        overheads = []
        # And average across multiple runs
        t1s = [time()]
        for _ in range(nrepeats):
            os.system(cmd + " >/dev/null 2>&1")
            t1s.append(time())
        t2s = []
        for _ in range(nrepeats):
            self.runner.run(cmd, **run_kwargs)
            t2s.append(time())
        get_dts = lambda x: [a - b for a, b in zip (x[1:], x[:-1])]
        dt1s = (get_dts(t1s))
        dt2s = (get_dts(t2s))
        dt1 = min(dt1s)
        dt2 = sum(dt2s) / nrepeats
        overhead = (round(100 * (dt2 / dt1 - 1.0), 2))
        # print(dt1, dt2, overhead)
        #print(dt1s, dt1)
        #print(dt2s, dt2, overhead)
        return overhead

    def track_overhead_echo(self):
        return self._get_overhead("echo")

    # 100ms chosen below as providing some sensible stability for me.
    # at 10ms -- too much variability
    def track_overhead_100ms(self):
        return self._get_overhead("sleep 0.1")

    def track_overhead_heavyout(self):
        # run busyloop for 100ms outputing as much as it could
        return self._get_overhead(heavyout_cmd)

    def track_overhead_heavyout_online_through(self):
        return self._get_overhead(heavyout_cmd,
                                  log_stderr='offline',  # needed to would get stuck
                                  log_online=True)

    def track_overhead_heavyout_online_process(self):
        return self._get_overhead(heavyout_cmd,
                                  log_stdout=lambda s: '',
                                  log_stderr='offline',  # needed to would get stuck
                                  log_online=True)

    # # Probably not really interesting, and good lord wobbles around 0
    # def track_overhead_heavyout_offline(self):
    #     return self._get_overhead(heavyout_cmd,
    #                               log_stdout='offline',
    #                               log_stderr='offline')

    # TODO: track the one with in/out, i.e. for those BatchedProcesses