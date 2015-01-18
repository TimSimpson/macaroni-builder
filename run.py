from colorama import Fore
from colorama import Back
from colorama import Style
from colorama import init
from proboscis import TestProgram

import tasks

if __name__ == "__main__":
    init()
    print(Fore.YELLOW + Back.BLUE + Style.BRIGHT + """
        Macaroni Builder
            Version      : {v}
            Release Notes: {r}
            Chocolate Ver: {c}
            Skip Deps?   : {s}  (enable by setting env var SKIP_DEPS)
        """.format(
        v = tasks.VERSION,
        r = tasks.RELEASE_NOTES,
        c = tasks.CHOCOLATEY_VERSION,
        s = tasks.SKIP_DEPS)
    )

    print(Fore.RESET + Back.RESET + Style.RESET_ALL)
    TestProgram().run_and_exit()
