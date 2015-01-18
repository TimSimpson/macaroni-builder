import os
from proboscis.asserts import *
from proboscis import test
import shutil
import subprocess
import sys


VERSION="0.3.0"
RELEASE_NOTES="Adds class and function templates."
CHOCOLATEY_VERSION="1"


def announce_settings():
    import options
    from colorama import Fore
    from colorama import Back
    from colorama import Style
    print(Fore.YELLOW + Back.BLUE + Style.BRIGHT + """
        Macaroni Builder
            Version      : {v}
            Release Notes: {r}
            Chocolate Ver: {c}
            Skip Deps?   : {s}
        """.format(
        v = VERSION,
        r = RELEASE_NOTES,
        c = CHOCOLATEY_VERSION,
        s = options.SKIP_DEPS)
    )
    print(Fore.RESET + Back.RESET + Style.RESET_ALL)


def step(*args, **kwargs):
    from options import SKIP_DEPS
    """Uses Proboscis test decorator to create an ordered step."""
    if SKIP_DEPS:
        if 'depends_on' in kwargs:
            if 'runs_after' not in kwargs:
                kwargs['runs_after'] = kwargs['depends_on']
            del kwargs['depends_on']
    return test(*args, **kwargs)


def dir(*args):
    """Returns a directory relative to "The Root."

    "The Root" is assumed to be one level above the directory of this project.

    """
    paths = [".."] + list(args)
    return str(os.path.abspath(os.path.join(*paths)))


def run(directory, args):
    """Runs a command."""
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
    app_dir = dir("Macaroni", "Main", "App")
    run(app_dir, "macaroni  --libraryRepoPath=..\Libraries "
        "--generatorPath=..\Generators -b --showPaths")
    run(dir(app_dir, "GeneratedSource"),
        "b2 -j4 -d+2 -q --toolset=msvc-12.0 address-model=32 threading=multi link=static release")


@step(groups=['release'], depends_on=[build_normal])
def build_tests():
    """Builds the tests in Next. """
    run(dir("Macaroni", "Next", "Tests"), "cavatappi -d -i")


@step(groups=['release'], depends_on=[build_normal, build_tests])
def build_release():
    """Builds the docs in "release." """
    run(dir("Macaroni", "Next", "Release"), "cavatappi -d -i")


@step(groups=['pureCpp'], depends_on=[build_release])
def build_pure_cpp():
    """
    Grab the "pureCpp" file made by the Release project, copy it somewhere
    clean, then try to build it to see if it correctly compiles.
    """
    src = dir("Macaroni", "Next", "Release", "target",
              "macaroni-%s-pureCpp" % VERSION)
    dst = dir("pureCppTest")
    copy_dir(src, dst)
    run(dir(dst),
        "b2 -d+2 -q -j8 link=static --address-model=32 release")


@step(groups=['site'], depends_on=[build_release])
def build_site():
    with open(dir("macaroni-site", "source", "www", "version.mdoc"), 'w') as f:
        f.write("""<~lua
            macaroni_version="%s"
            ~>""" % VERSION)
    # Copy docs
    release_target = dir("Macaroni", "Next", "Release", "target")
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


@step(groups=['chocolatey'], depends_on=[build_site])
def chocolatey():
    chocolatey_dir = dir("macaroni-chocolatey")
    full_choco_version = "%s.%s" % (VERSION, CHOCOLATEY_VERSION)

    def wipe_files():
        for file in ["Generators", "Libraries", "macaroni.exe", "Messages.txt"]:
            run(dir(chocolatey_dir, "tools"), "rm -rf ./%s" % file)
        run(chocolatey_dir, "rm -rf ./*.nupkg")

    def copy_files():
        src = dir("Macaroni", "Next", "Release", "target",
                  "macaroni-%s-windows-32" % VERSION)
        dst = dir(chocolatey_dir, "tools")
        copy_dir(src, dst)

    def change_template():
        with open("%s/macaroni.nuspec.template" % chocolatey_dir, 'r') as f:
            template = f.read()
        new_contents = (template.replace("{VERSION}", full_choco_version)
                                .replace("{NOTES}", RELEASE_NOTES))
        with open("%s/macaroni.nuspec" % chocolatey_dir, 'w') as f:
            f.write(new_contents)

    wipe_files()
    copy_files()
    change_template()

    # Build package
    run(chocolatey_dir, "cpack")
    # Test
    run(chocolatey_dir, "choco install macaroni -source %s -force" % chocolatey_dir)

    # Push
    cmd = ("nuget push macaroni.%s.nupkg -Source https://chocolatey.org/"
           % full_choco_version)

    print("RUN THIS!")
    print("cd %s" % chocolatey_dir)
    print(cmd)
    #run(chocolatey_dir, cmd)
