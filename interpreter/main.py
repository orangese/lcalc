"""Uses implementation of pure lambda calculus/lcalc language to interpreter .lc files/run in command-line mode. Also
uses error handling context manager. Called from lcalc excutable script.

Python version must be >=3.6, because error handling requires that dicts are insertion-ordered.
"""

import argparse
import os
import sys

from lang.error import ErrorHandler
from lang.shell import Shell
from lang.session import Session


def main():
    """Runs lcalc interpreter. Called from lcalc executable script."""
    assert sys.version_info >= (3, 6), "lcalc cannot be run with python < 3.6"

    with ErrorHandler() as error_handler:
        parser = argparse.ArgumentParser()
        parser.add_argument("file", help="file to interpret (if empty, command-line mode)", nargs="?")
        parser.add_argument("-s", "--sub", help="don't substitute named stmts after reduction", action="store_false")
        parser.add_argument("-v", "--verbose", help="verbose output during reduction", action="store_true")
        args = parser.parse_args()

        COMMON = os.path.join(__file__[:__file__.rfind("/")], "../common")

        if args.file is not None:
            sess = Session(error_handler, args.file, COMMON, cmd_line=False, sub=args.sub, verbose=args.verbose)
            sess.run()

        else:
            sess = Session(error_handler, Session.SH_FILE, COMMON, cmd_line=True, sub=args.sub, verbose=args.verbose)
            Shell(sess).cmdloop()
