"""`python -m calc` の入口。"""

import sys

from calc.cli import main

sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout, sys.stderr))
