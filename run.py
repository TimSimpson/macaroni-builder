from colorama import init
from proboscis import TestProgram
import options
import tasks

if __name__ == "__main__":
    init()
    tasks.announce_settings()
    TestProgram().run_and_exit()
