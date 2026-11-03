import sys

try:
    from adventure.ast import (
        Program,
        Location,
        Option,
        Statement,
        TextStmt,
        SetStmt,
        AddItemStmt,
        RemoveItemStmt,
        GotoStmt,
        EndStmt,
        IfStmt,
        WhileStmt,
        Expression,
        LiteralExpr,
        VarExpr,
        HasExpr,
        UnaryExpr,
        BinaryExpr,
    )
    from adventure.semantic import SemanticAnalyzer
except ImportError:
    from ast import (
        Program,
        Location,
        Option,
        Statement,
        TextStmt,
        SetStmt,
        AddItemStmt,
        RemoveItemStmt,
        GotoStmt,
        EndStmt,
        IfStmt,
        WhileStmt,
        Expression,
        LiteralExpr,
        VarExpr,
        HasExpr,
        UnaryExpr,
        BinaryExpr,
    )
    from semantic import SemanticAnalyzer


class Interpreter:
    def __init__(self, program_or_source, input_fn=input, output_fn=print):
        if isinstance(program_or_source, str):
            self.program = SemanticAnalyzer(program_or_source).analyze()
        else:
            self.program = program_or_source

        self.input_fn = input_fn
        self.output_fn = output_fn

        self.locations = {loc.name: loc for loc in self.program.locations}
        self.current_location = self.program.start_location
        self.inventory = list(self.program.inventory)
        self.state = dict(self.program.initial_state)

        self.next_location = None
        self.is_ended = False

    def eval_expr(self, expr):
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, VarExpr):
            return self.state[expr.name]

        if isinstance(expr, HasExpr):
            return expr.item in self.inventory

        if isinstance(expr, UnaryExpr):
            val = self.eval_expr(expr.operand)
            if expr.op == "NOT":
                return not val
            if expr.op == "-":
                return -val

        if isinstance(expr, BinaryExpr):
            l = self.eval_expr(expr.left)
            r = self.eval_expr(expr.right)
            if expr.op == "+":
                return l + r
            if expr.op == "-":
                return l - r
            if expr.op == "*":
                return l * r
            if expr.op == "/":
                return l // r
            if expr.op == "==":
                return l == r
            if expr.op == "!=":
                return l != r
            if expr.op == "<":
                return l < r
            if expr.op == "<=":
                return l <= r
            if expr.op == ">":
                return l > r
            if expr.op == ">=":
                return l >= r
            if expr.op == "AND":
                return bool(l and r)
            if expr.op == "OR":
                return bool(l or r)

        return None

    def exec_statement(self, stmt):
        if self.is_ended or self.next_location:
            return

        if isinstance(stmt, TextStmt):
            self.output_fn(stmt.message)
            return

        if isinstance(stmt, EndStmt):
            self.output_fn(stmt.message)
            self.is_ended = True
            return

        if isinstance(stmt, GotoStmt):
            self.next_location = stmt.target
            return

        if isinstance(stmt, SetStmt):
            self.state[stmt.variable] = self.eval_expr(stmt.value)
            return

        if isinstance(stmt, AddItemStmt):
            if stmt.item not in self.inventory:
                self.inventory.append(stmt.item)
            return

        if isinstance(stmt, RemoveItemStmt):
            if stmt.item in self.inventory:
                self.inventory.remove(stmt.item)
            return

        if isinstance(stmt, IfStmt):
            if self.eval_expr(stmt.condition):
                for s in stmt.then_branch:
                    self.exec_statement(s)
                    if self.is_ended or self.next_location:
                        break
            else:
                for s in stmt.else_branch:
                    self.exec_statement(s)
                    if self.is_ended or self.next_location:
                        break
            return

        if isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.condition):
                for s in stmt.body:
                    self.exec_statement(s)
                    if self.is_ended or self.next_location:
                        break
                if self.is_ended or self.next_location:
                    break
            return

    def run(self):
        self.output_fn(f"=== {self.program.story} ===\n")

        while not self.is_ended:
            if self.current_location not in self.locations:
                break

            loc = self.locations[self.current_location]

            for stmt in loc.statements:
                self.exec_statement(stmt)
                if self.is_ended or self.next_location:
                    break

            if self.is_ended:
                break

            if self.next_location:
                self.current_location = self.next_location
                self.next_location = None
                continue

            if not loc.options:
                break

            selectable = {}
            locked_hints = {}

            for opt in loc.options:
                key_lower = opt.key.lower()
                is_available = True
                if opt.condition is not None:
                    is_available = bool(self.eval_expr(opt.condition))

                if is_available:
                    selectable[key_lower] = opt
                else:
                    if opt.hint:
                        locked_hints[key_lower] = opt.hint

            self.output_fn("")
            for opt in loc.options:
                k = opt.key.lower()
                if k in selectable:
                    self.output_fn(f"[{opt.key}] {opt.text}")
                else:
                    hint = f" ({locked_hints[k]})" if k in locked_hints else ""
                    self.output_fn(f"[{opt.key}] {opt.text} [NEDOSTUPNO{hint}]")

            choice = self.input_fn("\nVaš izbor > ").strip().lower()

            if choice in ("q", "quit", "izlaz"):
                self.output_fn("\nIgra je prekinuta.")
                break

            if choice in selectable:
                opt = selectable[choice]
                self.output_fn("")
                for stmt in opt.body:
                    self.exec_statement(stmt)
                    if self.is_ended or self.next_location:
                        break

                if self.next_location:
                    self.current_location = self.next_location
                    self.next_location = None
            elif choice in locked_hints:
                self.output_fn(f"\n[!] {locked_hints[choice]}")
            else:
                self.output_fn("\n[!] Nepoznata ili trenutno nedostupna opcija.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        interp = Interpreter(code)
        interp.run()
    else:
        print("Upotreba: python -m adventure.interpreter <putanja_do_adv_fajla>")
