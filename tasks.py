import os
from proboscis.asserts import *
from proboscis import test
import shutil
import subprocess
import sys


VERSION="0.2.3"


def step(*args, **kwargs):
    if os.environ.get('SKIP_DEPS') is not None:
        if 'depends_on' in kwargs:
            if 'runs_after' not in kwargs:
                kwargs['runs_after'] = kwargs['depends_on']
            del kwargs['depends_on']
    return test(*args, **kwargs)


def dir(*args):
    paths = [".."] + list(args)
    return str(os.path.abspath(os.path.join(*paths)))


def run(directory, args):
    print("cd %s" % directory)
    print("%s" % args)
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


def unix_path(path):
    return path.replace("\\", "/").replace("C:/", "/cygdrive/c/")


def copy(src, dst):
    run(dir("."), "rsync -avz %s %s" % (unix_path(src), unix_path(dst)))


def copy_dir(src, dst):
    copy("%s/" % src, "%s/" % dst)


def upload(server, src, dst):
    dst = "%s:%s" % (server, unix_path(dst))
    run(dir("."), "rsync --chmod=a+r,Da+x -avz %s/ %s" % (unix_path(src), dst))


@step(groups=['build'])
def build_normal():
    """Builds Macaroni, then explicitly builds 32 bit release version."""
    app_dir = dir("trunk", "Main", "App")
    run(app_dir, "macaroni  --libraryRepoPath=..\Libraries "
        "--generatorPath=..\Generators -b --showPaths")
    run(dir(app_dir, "GeneratedSource"),
        "bjam -j4 -d+2 -q --toolset=msvc-12.0 address-model=32 threading=multi link=static release")


@step(groups=['release'], depends_on=[build_normal])
def build_tests():
    """Builds the tests in Next. """
    run(dir("trunk", "Next", "Tests"), "cavatappi -i")


@step(groups=['release'], depends_on=[build_normal, build_tests])
def build_release():
    """Builds the docs in "release." """
    run(dir("trunk", "Next", "Release"), "cavatappi -b")


@step(groups=['pureCpp'], depends_on=[build_release])
def build_pure_cpp():
    src = dir("trunk", "Next", "Release", "target",
              "macaroni-%s-pureCpp" % VERSION)
    dst = dir("pureCppTest")
    copy_dir(src, dst)
    run(dir(dst, "macaroni-%s-pureCpp" % VERSION),
        "bjam -d+2 -q -j8 link=static --address-model=32 release")


@step(groups=['site'], depends_on=[build_release])
def build_site():
    with open(dir("macaroni-site", "source", "www", "version.mdoc"), 'w') as f:
        f.write("""<~lua
            macaroni_version="%s"
            ~>""" % VERSION)
    # Copy docs
    release_target = dir("trunk", "Next", "Release", "target")
    site_target = dir("macaroni-site", "target", "www", "site")
    run(dir("macaroni-site"), "cavatappi -b")
    copy_dir(dir(release_target, "site"), dir(site_target, "docs"))

    copy(dir(site_target, "..", "..", "..", "source", "www", "_static", "default.css"),
         dir(site_target, "docs", "_static", "default.css"))
    # Copy downloads
    for suffix in ("windows-32", "pureCpp"):
        file_name = "macaroni-%s-%s.zip" % (VERSION, suffix)
        src = dir(release_target, file_name)
        dst = dir(site_target, "downloads", file_name)
        copy(src, dst)

@step(groups=['upload'], depends_on=[build_site])
def upload_site():
    upload("macaroni-web-page",
           dir("macaroni-site", "target", "www", "site"),
           "/bordertown/www/macaroni/")
