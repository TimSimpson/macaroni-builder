import os
from proboscis import TestProgram

os.environ.set('SKIP_DEPS', 'True')

import tasks

TestProgram().run_and_exit()
