from colorama import init
from proboscis import TestProgram
import options


options.SKIP_DEPS=True


if __name__ == "__main__":
    init()
    import tasks
    tasks.announce_settings()
    TestProgram().run_and_exit()
