import io
import contextlib
import timeit

from pyls.main import main
from test_endpoint import run_ls, run_pyls


def run():
    with contextlib.redirect_stdout(io.StringIO()):
        run_ls("test_fixture/sample_00")



print(timeit.timeit(run, number=1))


"""
 PYTHONPATH=src python -m timeit -n 10 \
  -s "from pyls.main import main; import os, contextlib; dn=open(os.devnull,'w')" \
  "with contextlib.redirect_stdout(dn): main(['test_fixture/sample_00'])" 

"""