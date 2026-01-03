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

    assert pyls_out == ls_out


def test_a_option():
    ls_out = run_ls("-a", "test_fixture")
    pyls_out = run_pyls("-a", "test_fixture")

    assert pyls_out == ls_out


def test_A_option():
    ls_out = run_ls("-A", "test_fixture")
    pyls_out = run_pyls("-A", "test_fixture")

    assert pyls_out == ls_out


def test_b_option():
    ls_out = run_ls("-b", "test_fixture")
    pyls_out = run_pyls("-b", "test_fixture")

    assert pyls_out == ls_out


def test_d_option():
    ls_out = run_ls("-d", "test_fixture")
    pyls_out = run_pyls("-d", "test_fixture")

    assert pyls_out == ls_out


def test_file_type_option():
    ls_out = run_ls("--file-type", "test_fixture")
    pyls_out = run_pyls("--file-type", "test_fixture")

    assert pyls_out == ls_out


def test_F_option():
    ls_out = run_ls("-F", "test_fixture")
    pyls_out = run_pyls("-F", "test_fixture")

    assert pyls_out == ls_out


def test_g_option():
    ls_out = run_ls("-g", "test_fixture")
    pyls_out = run_pyls("-g", "test_fixture")

    assert pyls_out == ls_out


def test_hide_option():
    ls_out = run_ls("--hide", "*01", "test_fixture")
    pyls_out = run_pyls("--hide", "*01", "test_fixture")

    assert pyls_out == ls_out


def test_i_option():
    pyls_out = run_pyls("-i", "test_fixture")

    expected = "5810 sample_00  5836 sample_01\n"
    assert pyls_out == expected


def test_I_option():
    ls_out = run_ls("-I", "*01", "test_fixture")
    pyls_out = run_pyls("-I", "*01", "test_fixture")

    assert pyls_out == ls_out


def test_l_h_option():
    ls_out = run_ls("-l", "-h")
    pyls_out = run_pyls("-l", "-h")

    ls_total = ls_out.strip().split("\n")[0]
    pyls_total = pyls_out.strip().split("\n")[0]

    assert pyls_total == ls_total


def test_p_option():
    ls_out = run_ls("-p", "test_fixture")
    pyls_out = run_pyls("-p", "test_fixture")

    assert pyls_out == ls_out


def test_Q_option():
    ls_out = run_ls("-Q", "test_fixture")
    pyls_out = run_pyls("-Q", "test_fixture")

    assert pyls_out == ls_out


def test_r_option():
    ls_out = run_ls("-r", "test_fixture")
    pyls_out = run_pyls("-r", "test_fixture")

    assert pyls_out == ls_out


def test_n_option():
    ls_out = run_ls("-n", "test_fixture")
    pyls_out = run_pyls("-n", "test_fixture")

    assert pyls_out == ls_out


def test_l_option():
    ls_out = run_ls("-l", "test_fixture")
    pyls_out = run_pyls("-l", "test_fixture")

    assert pyls_out == ls_out


def test_R_option():
    pyls_out = run_pyls("-R", "test_fixture/sample_00")

    assert (
        pyls_out
        == """test_fixture/sample_00:
dir_a  file_0000.txt  file_0002.txt  file_0004.txt  file_0006.txt  file_0008.txt  
dir_b  file_0001.txt  file_0003.txt  file_0005.txt  file_0007.txt  file_0009.txt  
test_fixture/sample_00/dir_a:
a_0000.txt  a_0001.txt  a_0002.txt  a_0003.txt  a_0004.txt

test_fixture/sample_00/dir_b:
b_0000.txt  b_0002.txt  b_0004.txt  b_0006.txt  
b_0001.txt  b_0003.txt  b_0005.txt  b_0007.txt  
"""
    )


def test_s_option():
    ls_out = run_ls("-s", "test_fixture")
    pyls_out = run_pyls("-s", "test_fixture")

    assert pyls_out == ls_out


def test_S_option():
    ls_out = run_ls("-S", "test_fixture")
    pyls_out = run_pyls("-S", "test_fixture")

    assert pyls_out == ls_out


def test_t_option():
    ls_out = run_ls("-t", "test_fixture")
    pyls_out = run_pyls("-t", "test_fixture")

    assert pyls_out == ls_out


def test_T_option():
    ls_out = run_ls("-T", "4", "test_fixture")
    pyls_out = run_pyls("-T", "4", "test_fixture")

    assert pyls_out == ls_out


def test_U_option():
    ls_out = run_ls("-U", "test_fixture")
    pyls_out = run_pyls("-U", "test_fixture")

    assert pyls_out == ls_out


def test_X_option():
    ls_out = run_ls("-X", "test_fixture")
    pyls_out = run_pyls("-X", "test_fixture")

    assert pyls_out == ls_out


def test_1_option():
    ls_out = run_ls("-1", "test_fixture")
    pyls_out = run_pyls("-1", "test_fixture")

    assert pyls_out == ls_out


def test_w_option():
    ls_out = run_ls("-w", "90", "test_fixture")
    pyls_out = run_pyls("-w", "90", "test_fixture")

    assert pyls_out == ls_out
