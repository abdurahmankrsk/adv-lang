import sys

try:
    from adventure.tokens import EOF
    from adventure.lexer import Lexer
    from adventure.errors import ParseError
    from adventure.ast import (
        Program,
        Location,
        Option,
        TextStmt,
        SetStmt,
        AddItemStmt,
        RemoveItemStmt,
        GotoStmt,
        EndStmt,
        IfStmt,
        WhileStmt,
        LiteralExpr,
        VarExpr,
        HasExpr,
        UnaryExpr,
        BinaryExpr,
    )
except ImportError:
    from tokens import EOF
    from lexer import Lexer
    from errors import ParseError
    from ast import (
        Program,
        Location,
        Option,
        TextStmt,
        SetStmt,
        AddItemStmt,
        RemoveItemStmt,
        GotoStmt,
        EndStmt,
        IfStmt,
        WhileStmt,
        LiteralExpr,
        VarExpr,
        HasExpr,
        UnaryExpr,
        BinaryExpr,
    )


class Parser:
    def __init__(self, tokens_or_source):
        if isinstance(tokens_or_source, str):
            self.tokens = Lexer(tokens_or_source).tokenize()
        else:
            self.tokens = tokens_or_source
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos]

    def _previous(self):
        return self.tokens[self.pos - 1]

    def _is_at_end(self):
        return self._peek().type == EOF

    def _check(self, token_type):
        if self._is_at_end():
            return token_type == EOF
        return self._peek().type == token_type

    def _advance(self):
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _match(self, *token_types):
        for tt in token_types:
            if self._check(tt):
                self._advance()
                return True
        return False

    def _consume(self, token_type, error_message):
        if self._check(token_type):
            return self._advance()
        tok = self._peek()
        raise ParseError(error_message, tok.line, tok.column)

    def parse(self):
        story = ""
        start_location = ""
        items = []
        inventory = []
        state = {}

        story_tok = self._consume("STORY", "Očekivana deklaracija STORY na početku programa")
        story = self._consume("STRING", "Očekivan naziv priče nakon STORY").value

        self._consume("START_LOCATION", "Očekivana deklaracija START_LOCATION")
        start_location = self._consume("IDENT", "Očekivano ime početne lokacije").value

        self._consume("ITEMS", "Očekivana deklaracija ITEMS")
        self._consume("LBRACKET", "Očekivana '[' nakon ITEMS")
        while not self._check("RBRACKET") and not self._is_at_end():
            item_tok = self._consume("IDENT", "Očekivano ime predmeta u ITEMS")
            items.append(item_tok.value)
            if not self._check("RBRACKET"):
                self._consume("COMMA", "Očekivan ',' između predmeta u ITEMS")
        self._consume("RBRACKET", "Očekivana ']' nakon ITEMS liste")

        self._consume("INVENTORY", "Očekivana deklaracija INVENTORY")
        self._consume("LBRACKET", "Očekivana '[' nakon INVENTORY")
        while not self._check("RBRACKET") and not self._is_at_end():
            item_tok = self._consume("IDENT", "Očekivano ime predmeta u INVENTORY")
            inventory.append(item_tok.value)
            if not self._check("RBRACKET"):
                self._consume("COMMA", "Očekivan ',' između predmeta u INVENTORY")
        self._consume("RBRACKET", "Očekivana ']' nakon INVENTORY liste")

        self._consume("STATE", "Očekivana deklaracija STATE")
        self._consume("LBRACE", "Očekivana '{' nakon STATE")
        while not self._check("RBRACE") and not self._is_at_end():
            var_tok = self._consume("IDENT", "Očekivano ime promenljive u STATE")
            self._consume("ASSIGN", "Očekivano '=' u deklaraciji promenljive u STATE")
            val = self._parse_state_value()
            state[var_tok.value] = val
            if not self._check("RBRACE"):
                self._consume("COMMA", "Očekivan ',' između promenljivih u STATE")
        self._consume("RBRACE", "Očekivana '}' na kraju STATE bloka")

        locations = []
        while not self._is_at_end():
            locations.append(self._parse_location())

        return Program(
            story=story,
            start_location=start_location,
            items=items,
            inventory=inventory,
            initial_state=state,
            locations=locations,
            line=story_tok.line,
            column=story_tok.column,
        )

    def _parse_state_value(self):
        if self._match("NUMBER", "STRING", "BOOL"):
            return self._previous().value
        if self._match("MINUS"):
            num = self._consume("NUMBER", "Očekivan broj nakon znaka minus")
            return -num.value
        tok = self._peek()
        raise ParseError(f"Neočekivana vrednost u STATE: {tok.value!r}", tok.line, tok.column)

    def _parse_location(self):
        start = self._consume("LOCATION", "Očekivana ključna reč LOCATION")
        name_tok = self._consume("IDENT", "Očekivano ime lokacije")
        self._consume("LBRACE", "Očekivana '{' nakon imena lokacije")
        statements = []
        options = []
        while not self._check("RBRACE") and not self._is_at_end():
            if self._check("OPTION"):
                options.append(self._parse_option())
            else:
                statements.append(self._parse_statement())
        self._consume("RBRACE", "Očekivana '}' na kraju lokacije")
        return Location(
            name=name_tok.value,
            statements=statements,
            options=options,
            line=start.line,
            column=start.column,
        )

    def _parse_option(self):
        start = self._consume("OPTION", "Očekivana ključna reč OPTION")
        key_tok = self._consume("IDENT", "Očekivana oznaka opcije")
        text_tok = self._consume("STRING", "Očekivan tekst opcije")
        condition = None
        hint = None
        while self._check("IF") or self._check("HINT"):
            if self._match("IF"):
                condition = self._parse_expression()
            elif self._match("HINT"):
                hint = self._consume("STRING", "Očekivan tekst pomoći nakon HINT").value
        self._consume("LBRACE", "Očekivana '{' nakon opcije")
        body = []
        while not self._check("RBRACE") and not self._is_at_end():
            body.append(self._parse_statement())
        self._consume("RBRACE", "Očekivana '}' na kraju opcije")
        return Option(
            key=key_tok.value,
            text=text_tok.value,
            condition=condition,
            hint=hint,
            body=body,
            line=start.line,
            column=start.column,
        )

    def _parse_statement(self):
        if self._match("TEXT"):
            start = self._previous()
            msg = self._consume("STRING", "Očekivan string nakon TEXT").value
            return TextStmt(message=msg, line=start.line, column=start.column)

        if self._match("SET"):
            start = self._previous()
            var_tok = self._consume("IDENT", "Očekivano ime promenljive nakon SET")
            self._consume("ASSIGN", "Očekivano '=' u SET naredbi")
            val_expr = self._parse_expression()
            return SetStmt(
                variable=var_tok.value,
                value=val_expr,
                line=start.line,
                column=start.column,
            )

        if self._match("ADD_ITEM"):
            start = self._previous()
            item_tok = self._consume("IDENT", "Očekivano ime predmeta nakon ADD_ITEM")
            return AddItemStmt(
                item=item_tok.value,
                line=start.line,
                column=start.column,
            )

        if self._match("REMOVE_ITEM"):
            start = self._previous()
            item_tok = self._consume("IDENT", "Očekivano ime predmeta nakon REMOVE_ITEM")
            return RemoveItemStmt(
                item=item_tok.value,
                line=start.line,
                column=start.column,
            )

        if self._match("GOTO"):
            start = self._previous()
            target_tok = self._consume("IDENT", "Očekivano ime lokacije nakon GOTO")
            return GotoStmt(
                target=target_tok.value,
                line=start.line,
                column=start.column,
            )

        if self._match("END"):
            start = self._previous()
            msg = self._consume("STRING", "Očekivana poruka kraja nakon END").value
            return EndStmt(message=msg, line=start.line, column=start.column)

        if self._match("IF"):
            start = self._previous()
            condition = self._parse_expression()
            self._consume("LBRACE", "Očekivana '{' nakon IF uslova")
            then_branch = []
            while not self._check("RBRACE") and not self._is_at_end():
                then_branch.append(self._parse_statement())
            self._consume("RBRACE", "Očekivana '}' na kraju IF bloka")
            else_branch = []
            if self._match("ELSE"):
                self._consume("LBRACE", "Očekivana '{' nakon ELSE")
                while not self._check("RBRACE") and not self._is_at_end():
                    else_branch.append(self._parse_statement())
                self._consume("RBRACE", "Očekivana '}' na kraju ELSE bloka")
            return IfStmt(
                condition=condition,
                then_branch=then_branch,
                else_branch=else_branch,
                line=start.line,
                column=start.column,
            )

        if self._match("WHILE"):
            start = self._previous()
            condition = self._parse_expression()
            self._consume("LBRACE", "Očekivana '{' nakon WHILE uslova")
            body = []
            while not self._check("RBRACE") and not self._is_at_end():
                body.append(self._parse_statement())
            self._consume("RBRACE", "Očekivana '}' na kraju WHILE bloka")
            return WhileStmt(
                condition=condition,
                body=body,
                line=start.line,
                column=start.column,
            )

        tok = self._peek()
        raise ParseError(f"Neočekivana naredba: {tok.value!r}", tok.line, tok.column)

    def _parse_expression(self):
        return self._parse_or()

    def _parse_or(self):
        expr = self._parse_and()
        while self._match("OR"):
            op_tok = self._previous()
            right = self._parse_and()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_and(self):
        expr = self._parse_equality()
        while self._match("AND"):
            op_tok = self._previous()
            right = self._parse_equality()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_equality(self):
        expr = self._parse_comparison()
        while self._match("EQ", "NEQ"):
            op_tok = self._previous()
            right = self._parse_comparison()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_comparison(self):
        expr = self._parse_term()
        while self._match("LT", "GT", "LE", "GE"):
            op_tok = self._previous()
            right = self._parse_term()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_term(self):
        expr = self._parse_factor()
        while self._match("PLUS", "MINUS"):
            op_tok = self._previous()
            right = self._parse_factor()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_factor(self):
        expr = self._parse_unary()
        while self._match("STAR", "SLASH"):
            op_tok = self._previous()
            right = self._parse_unary()
            expr = BinaryExpr(
                left=expr,
                op=op_tok.value,
                right=right,
                line=op_tok.line,
                column=op_tok.column,
            )
        return expr

    def _parse_unary(self):
        if self._match("NOT", "MINUS"):
            op_tok = self._previous()
            operand = self._parse_unary()
            return UnaryExpr(
                op=op_tok.value,
                operand=operand,
                line=op_tok.line,
                column=op_tok.column,
            )
        return self._parse_primary()

    def _parse_primary(self):
        if self._match("HAS"):
            start = self._previous()
            item_tok = self._consume("IDENT", "Očekivano ime predmeta nakon HAS")
            return HasExpr(item=item_tok.value, line=start.line, column=start.column)

        if self._match("NUMBER", "STRING", "BOOL"):
            tok = self._previous()
            return LiteralExpr(value=tok.value, line=tok.line, column=tok.column)

        if self._match("IDENT"):
            tok = self._previous()
            return VarExpr(name=tok.value, line=tok.line, column=tok.column)

        if self._match("LPAREN"):
            expr = self._parse_expression()
            self._consume("RPAREN", "Očekivana zatvorena zagrada ')'")
            return expr

        tok = self._peek()
        raise ParseError(f"Neočekivan token u izrazu: {tok.value!r}", tok.line, tok.column)
