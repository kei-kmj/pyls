import subprocess


def run_ls(*args, cwd=None):
    result = subprocess.run(
        ["ls", "-C", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout

def run_pyls(*args, cwd=None):
    result = subprocess.run(
        ["uv", "run", "pyls", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout



def test_no_options():
    ls_out = run_ls("test_fixture")
    pyls_out = run_pyls("test_fixture")

    assert ls_out == pyls_out


def test_a_option():
    ls_out = run_ls("-a", "test_fixture")
    pyls_out = run_pyls("-a", "test_fixture")

    assert ls_out == pyls_out


def test_A_option():
    ls_out = run_ls("-A", "test_fixture")
    pyls_out = run_pyls("-A", "test_fixture")

    assert ls_out == pyls_out


def test_F_option():
    ls_out = run_ls("-F", "test_fixture")
    pyls_out = run_pyls("-F", "test_fixture")

    assert ls_out == pyls_out


def test_i_option():
    ls_out = run_ls("-i", "test_fixture")
    pyls_out = run_pyls("-i", "test_fixture")

    assert ls_out == pyls_out


def test_p_option():
    ls_out = run_ls("-p", "test_fixture")
    pyls_out = run_pyls("-p", "test_fixture")

    assert ls_out == pyls_out


def test_Q_option():
    ls_out = run_ls("-Q", "test_fixture")
    pyls_out = run_pyls("-Q", "test_fixture")

    assert ls_out == pyls_out


def test_r_option():
    ls_out = run_ls("-r", "test_fixture")
    pyls_out = run_pyls("-r", "test_fixture")

    assert ls_out == pyls_out


def test_s_option():
    ls_out = run_ls("-s", "test_fixture")
    pyls_out = run_pyls("-s", "test_fixture")

    assert ls_out == pyls_out