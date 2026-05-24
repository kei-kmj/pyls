import time

from tests.test_endpoint import run_ls, run_pyls

N = 1

def bench_ls():

    start_time = time.time()

    for _ in range(N):
        run_ls("test_fixture/sample_00")

    end_time = time.time()
    print(f"ls benchmark: {end_time - start_time:.6f} seconds")


def bench_pyls():

    start_time = time.time()

    for _ in range(N):
        run_pyls("test_fixture/sample_00")

    end_time = time.time()
    print(f"pyls benchmark: {end_time - start_time:.6f} seconds")

if __name__ == "__main__":
    bench_ls()
    bench_pyls()
