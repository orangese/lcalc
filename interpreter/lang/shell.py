"""Handles interactive/command-line mode for lcalc interpreter. Uses cmd as backend."""

import cmd


class Shell(cmd.Cmd):
    """Lambda calculus interpreter shell."""
    intro = "Lambda calculus interpreter :: Python backend\nType '?' or 'help' for more information."
    prompt = "> "
    secondary_prompt = ". "  # used for line continutations
    _tmp_prompt = "> "       # also used for prompt swapping in line continuations

    def __init__(self, sess, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sess = sess

        self._tmp_line = ""
        self.line_num = 0

    def default(self, line):
        """Executes arbitrary lcalc command."""
        with self.sess.error_handler:  # needed because cmd.Cmd automatically exits on Exception
            self.line_num += 1
            line, add_to_prev = self.sess.preprocess_line(self._tmp_line + line, self.line_num, self._tmp_line)

            if add_to_prev:
                self._tmp_line = line
                self.prompt = self.secondary_prompt
            else:
                self._tmp_line = ""
                self.prompt = self._tmp_prompt

                if line and not line.isspace():
                    self.sess.add(line, self.line_num)
                    self.sess.run()

    def do_help(self, arg):
        """Doesn't return docs, but rather a short intro."""
        print(
            "Welcome to the lcalc interpreter!\n\n"
            "Lambda calculus is a Turing-complete language created by Alonzo Church. This \n"
            "interpreter supports pure lambda calculus as imagined by Church as well as \n"
            "named functions, file imports, and define directives.\n\n"
            "Try it out by typing 'I := λx.x'.This will bind the lambda term 'λx.x' to a \n"
            "name 'I'. Next, try typing 'I y'. This will apply 'y' to 'λx.x', giving 'y' as \n"
            "the result.\n\n"
            "This project was created solely for fun and to give the author a sense of how \n"
            "powerful lambda calculus can be. As a result, nothing is optimized (eg: \n"
            "numbers are implemented as Church numerals, so even basic arithmetic is \n"
            "*extremely* slow)."
        )

    def emptyline(self):
        """Do not repeat previous command on empty line."""
        return ""

    def do_EOF(self, arg):
        """Exits interpreter."""
        print()
        return self.do_exit(arg)

    def do_exit(self, arg):
        """Exits interpreter."""
        return True
