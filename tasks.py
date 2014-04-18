import os
from proboscis.asserts import *
from proboscis import test
import shutil
import subprocess


def dir(*args):
    paths = [".."] + list(args)
    return str(os.path.join(*paths))


def run(directory, args):
    print("cd %s" % directory)
    proc = subprocess.Popen(
        args,
        bufsize=1,
        cwd=directory,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    while proc.poll() is None:
        line = proc.stdout.readline()
        sys.stdout.write(line)
    assert_equal(0, proc.returncode,
        "Process had non-zero return code.")


@test(groups=['release'])
def build_release():
    run(dir("trunk", "Next", "Release"), "cavatappi -b")


@test(groups=['site'], depends_on=['release'])
def build_site():
    run(dir("macaroni-site"), "cavatappi -b")
    src = dir("trunk", "Next", "Release", "target", "www",
              "site", "docs")
    dst = dir("macaroni-site", "target", "www", "site", "docs")
    shutil.rmtree(dst)
    shutil.copytree(src, dst)
