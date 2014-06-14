from proboscis import TestProgram

import options


options.SKIP_DEPS=True


import tasks

TestProgram().run_and_exit()
