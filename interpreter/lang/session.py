"""Session control for lcalc language. Implementation of lexical parsing to run the lc interpreter, either in command
line mode or file interpretation mode.
"""

import os

from lang.error import GenericException
from lang.lexical import DefineStmt, ExecStmt, ImportStmt, Grammar, NamedFunc


class Session:
    """Governs a lc session, with control over scope of named funcs."""
    SH_FILE = "<in>"  # command-line interpreter filename

    def __init__(self, error_handler, path, common_path, **flags):
        self.error_handler = error_handler
        self.error_handler.register_file(path)

        self.path = path                # used for error messages
        self.common_path = common_path  # path to common lcalc lib

        self.defines = []    # list of define directives
        self.namespace = {}  # dict of name.expr: NamedFuncs that exist in the current session
        self.to_exec = {}    # dict of line num: ExecStmts to execute

        self.cmd_line = flags.get("cmd_line", False)  # whether or not in command-line mode
        self.sub = flags.get("sub", False)            # whether or not to sub NamedStmts after reduction of ExecStmt
        self.verbose = flags.get("verbose", False)    # whether or not to be verbose during ExecStmt reduction

        self.error_handler.fatal = not self.cmd_line
        self.error_handler.verbose = self.verbose

        if path != Session.SH_FILE:
            exprs = []
            add_to_prev = False

            try:
                with open(path, "r") as file:
                    for line_num, line in enumerate(file):
                        __, add_to_prev = self.preprocess_line(line, line_num + 1, add_to_prev, exprs)
            except OSError:
                raise GenericException("'{}' could not be opened", path, diagnosis=False)

            for expr in exprs:
                self.add(*expr)

        elif not self.cmd_line:
            raise GenericException("'<in>' is a reserved filename")

    @staticmethod
    def preprocess_line(line, line_num, add_to_prev, exprs=None):
        """Preprocesses a line from a file or command-line. In command-line mode, exprs can be ignored (used to keep
        track of file's exprs), but add_to_prev will indicate whether a line continuation is necessary. Returns
        updated value of line and add_to_prev. Must be called before calling run.
        """
        if ";;" in line:
            line = line[:line.index(";;")]  # get rid of comments

        line = Grammar.preprocess(line)
        if exprs is not None:
            if not line.isspace() and line and not add_to_prev:
                exprs.append((line, line_num))
            elif add_to_prev:
                popped = exprs.pop()
                prev = popped[0] if len(popped) == 2 else popped[-1]
                line = popped[0] + line
                exprs.append((line, line_num, prev))

        return line, line.count("(") > line.count(")")

    def add(self, expr, line_num, original_expr=None):
        """Adds Grammar object to the current session. Beta-reduction is lazy and is delayed until run is called.
        However, expansion of NamedStmts that use other NamedStmts in their definitions is not lazy and is handled in
        this function, rather than in run.
        """
        self.error_handler.register_line(self.path, expr, line_num)  # in case error is raised

        for stmt in self.defines:
            expr = stmt.replace(expr)
        stmt = Grammar.infer(expr, original_expr)

        if isinstance(stmt, ImportStmt):
            for path in self._get_paths(stmt.path):
                flags = dict(cmd_line=self.cmd_line, sub=self.sub, verbose=self.verbose)
                loaded_module = Session(self.error_handler, path, self.common_path, **flags)

                self.namespace = {**loaded_module.namespace, **self.namespace}
                # on import, ExecStmts from the imported module will not be run
                # local namespace also takes precedence over the loaded module's namespace in the case of name conflicts

        elif isinstance(stmt, DefineStmt):
            self.defines.append(stmt)

        elif isinstance(stmt, NamedFunc):
            stmt.register_namespace(self.namespace)  # NamedStmt substitution is eager
            self.namespace[stmt.name.expr] = stmt

        elif isinstance(stmt, ExecStmt):
            stmt.register_namespace(self.namespace)
            self.to_exec[line_num] = stmt

        self.error_handler.remove_line(self.path)  # error was not raised

    def run(self):
        """Runs this session's executable statements by beta-reducing them."""
        for line_num, exec_stmt in list(self.to_exec.items()):
            self.error_handler.register_line(self.path, str(exec_stmt), line_num)

            try:
                print(exec_stmt.execute(self.error_handler, self.sub))
            finally:
                if self.cmd_line:
                    del self.to_exec[line_num]

            self.error_handler.remove_line(self.path)

    def _get_paths(self, path):
        """Returns [path] if path != 'common' else absolute paths of common .lc files."""
        if path == "common":
            return [os.path.abspath(f"{self.common_path}/{file}") for file in sorted(os.listdir(self.common_path))]
        return [os.path.abspath(path)]
