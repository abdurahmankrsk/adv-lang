import sys

try:
    from adventure.errors import SemanticError
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
    from adventure.parser import Parser
except ImportError:
    from errors import SemanticError
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
    from parser import Parser


class SemanticAnalyzer:
    def __init__(self, program_or_source):
        if isinstance(program_or_source, str):
            self.program = Parser(program_or_source).parse()
        else:
            self.program = program_or_source

        self.locations_map = {}
        self.items_set = set()
        self.symbol_table = {}

    def _type_name_of_val(self, val):
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, str):
            return "str"
        return "unknown"

    def analyze(self):
        seen_items = set()
        for item in self.program.items:
            if item in seen_items:
                raise SemanticError(
                    f"Duplikat predmeta u ITEMS: {item!r}",
                    self.program.line,
                    self.program.column,
                )
            seen_items.add(item)
        self.items_set = seen_items

        seen_inv = set()
        for item in self.program.inventory:
            if item not in self.items_set:
                raise SemanticError(
                    f"Predmet {item!r} u inventaru nije deklarisan u ITEMS",
                    self.program.line,
                    self.program.column,
                )
            if item in seen_inv:
                raise SemanticError(
                    f"Duplikat predmeta u INVENTORY: {item!r}",
                    self.program.line,
                    self.program.column,
                )
            seen_inv.add(item)

        for var_name, init_val in self.program.initial_state.items():
            self.symbol_table[var_name] = self._type_name_of_val(init_val)

        for loc in self.program.locations:
            if loc.name in self.locations_map:
                raise SemanticError(
                    f"Duplikat imena lokacije: {loc.name!r}",
                    loc.line,
                    loc.column,
                )
            self.locations_map[loc.name] = loc

        if self.program.start_location not in self.locations_map:
            raise SemanticError(
                f"Početna lokacija {self.program.start_location!r} nije definisana",
                self.program.line,
                self.program.column,
            )

        for loc in self.program.locations:
            self._analyze_location(loc)

        return self.program

    def _analyze_location(self, loc):
        seen_keys = set()
        for opt in loc.options:
            if opt.key in seen_keys:
                raise SemanticError(
                    f"Duplikat oznake opcije {opt.key!r} u lokaciji {loc.name!r}",
                    opt.line,
                    opt.column,
                )
            seen_keys.add(opt.key)

        for stmt in loc.statements:
            self._analyze_statement(stmt)

        for opt in loc.options:
            self._analyze_option(opt)

    def _analyze_option(self, opt):
        if opt.condition is not None:
            t = self._eval_expr_type(opt.condition)
            if t != "bool":
                raise SemanticError(
                    f"Uslov u opciji {opt.key!r} mora biti logičkog tipa (bool), dobijen {t}",
                    opt.line,
                    opt.column,
                )
        for stmt in opt.body:
            self._analyze_statement(stmt)

    def _analyze_statement(self, stmt):
        if isinstance(stmt, TextStmt) or isinstance(stmt, EndStmt):
            return

        if isinstance(stmt, GotoStmt):
            if stmt.target not in self.locations_map:
                raise SemanticError(
                    f"Nepoznata lokacija u GOTO naredbi: {stmt.target!r}",
                    stmt.line,
                    stmt.column,
                )
            return

        if isinstance(stmt, AddItemStmt):
            if stmt.item not in self.items_set:
                raise SemanticError(
                    f"Nepoznat predmet u ADD_ITEM: {stmt.item!r}",
                    stmt.line,
                    stmt.column,
                )
            return

        if isinstance(stmt, RemoveItemStmt):
            if stmt.item not in self.items_set:
                raise SemanticError(
                    f"Nepoznat predmet u REMOVE_ITEM: {stmt.item!r}",
                    stmt.line,
                    stmt.column,
                )
            return

        if isinstance(stmt, SetStmt):
            if stmt.variable not in self.symbol_table:
                raise SemanticError(
                    f"Nedeklarisana promenljiva u SET: {stmt.variable!r}",
                    stmt.line,
                    stmt.column,
                )
            var_type = self.symbol_table[stmt.variable]
            expr_type = self._eval_expr_type(stmt.value)
            if var_type != expr_type:
                raise SemanticError(
                    f"Nekompatibilni tipovi u SET za {stmt.variable!r}: očekivan {var_type}, dobijen {expr_type}",
                    stmt.line,
                    stmt.column,
                )
            return

        if isinstance(stmt, IfStmt):
            cond_type = self._eval_expr_type(stmt.condition)
            if cond_type != "bool":
                raise SemanticError(
                    f"Uslov u IF naredbi mora biti logičkog tipa (bool), dobijen {cond_type}",
                    stmt.line,
                    stmt.column,
                )
            for s in stmt.then_branch:
                self._analyze_statement(s)
            for s in stmt.else_branch:
                self._analyze_statement(s)
            return

        if isinstance(stmt, WhileStmt):
            cond_type = self._eval_expr_type(stmt.condition)
            if cond_type != "bool":
                raise SemanticError(
                    f"Uslov u WHILE petlji mora biti logičkog tipa (bool), dobijen {cond_type}",
                    stmt.line,
                    stmt.column,
                )
            for s in stmt.body:
                self._analyze_statement(s)
            return

        raise SemanticError(f"Nepoznata naredba: {stmt!r}", stmt.line, stmt.column)

    def _eval_expr_type(self, expr):
        if isinstance(expr, LiteralExpr):
            return self._type_name_of_val(expr.value)

        if isinstance(expr, VarExpr):
            if expr.name not in self.symbol_table:
                raise SemanticError(
                    f"Nedeklarisana promenljiva u izrazu: {expr.name!r}",
                    expr.line,
                    expr.column,
                )
            return self.symbol_table[expr.name]

        if isinstance(expr, HasExpr):
            if expr.item not in self.items_set:
                raise SemanticError(
                    f"Nepoznat predmet u HAS izrazu: {expr.item!r}",
                    expr.line,
                    expr.column,
                )
            return "bool"

        if isinstance(expr, UnaryExpr):
            t = self._eval_expr_type(expr.operand)
            if expr.op == "NOT":
                if t != "bool":
                    raise SemanticError(
                        f"Operator NOT očekuje tip bool, dobijen {t}",
                        expr.line,
                        expr.column,
                    )
                return "bool"
            if expr.op == "-":
                if t != "int":
                    raise SemanticError(
                        f"Unarni minus očekuje tip int, dobijen {t}",
                        expr.line,
                        expr.column,
                    )
                return "int"
            raise SemanticError(f"Nepoznat unarni operator: {expr.op!r}", expr.line, expr.column)

        if isinstance(expr, BinaryExpr):
            lt = self._eval_expr_type(expr.left)
            rt = self._eval_expr_type(expr.right)

            if expr.op in ("+", "-", "*", "/"):
                if expr.op == "+" and lt == "str" and rt == "str":
                    return "str"
                if lt != "int" or rt != "int":
                    raise SemanticError(
                        f"Aritmetički operator {expr.op!r} očekuje operande tipa int, dobijeni {lt} i {rt}",
                        expr.line,
                        expr.column,
                    )
                return "int"

            if expr.op in ("<", ">", "<=", ">="):
                if lt != "int" or rt != "int":
                    raise SemanticError(
                        f"Relacioni operator {expr.op!r} očekuje operande tipa int, dobijeni {lt} i {rt}",
                        expr.line,
                        expr.column,
                    )
                return "bool"

            if expr.op in ("==", "!="):
                if lt != rt:
                    raise SemanticError(
                        f"Poređenje jednakosti {expr.op!r} očekuje operande istog tipa, dobijeni {lt} i {rt}",
                        expr.line,
                        expr.column,
                    )
                return "bool"

            if expr.op in ("AND", "OR"):
                if lt != "bool" or rt != "bool":
                    raise SemanticError(
                        f"Logički operator {expr.op!r} očekuje operande tipa bool, dobijeni {lt} i {rt}",
                        expr.line,
                        expr.column,
                    )
                return "bool"

            raise SemanticError(f"Nepoznat binarni operator: {expr.op!r}", expr.line, expr.column)

        raise SemanticError(f"Nepoznat izraz: {expr!r}", expr.line, expr.column)
