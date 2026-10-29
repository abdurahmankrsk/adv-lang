import sys

try:
    from adventure.tokens import (
        KEYWORDS,
        IDENT,
        NUMBER,
        STRING,
        BOOL,
        EOF,
        SINGLE_CHAR_TOKENS,
        TWO_CHAR_TOKENS,
        Token,
    )
    from adventure.errors import LexError
except ImportError:
    from tokens import (
        KEYWORDS,
        IDENT,
        NUMBER,
        STRING,
        BOOL,
        EOF,
        SINGLE_CHAR_TOKENS,
        TWO_CHAR_TOKENS,
        Token,
    )
    from errors import LexError


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def _peek(self, offset=0):
        target_pos = self.pos + offset
        if target_pos >= self.length:
            return None
        return self.source[target_pos]

    def _advance(self):
        if self.pos >= self.length:
            return None
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace_and_comments(self):
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch in " \t\r":
                self._advance()
            elif ch == "\n":
                self._advance()
            elif ch == "#":
                while self.pos < self.length and self.source[self.pos] != "\n":
                    self._advance()
            else:
                break

    def _read_string(self):
        start_line = self.line
        start_col = self.column
        self._advance()
        chars = []
        while True:
            if self.pos >= self.length:
                raise LexError("Nezatvoren string literal", start_line, start_col)
            ch = self._peek()
            if ch == '"':
                self._advance()
                break
            elif ch == "\\":
                self._advance()
                if self.pos >= self.length:
                    raise LexError("Nezatvoren string literal nakon escape karaktera", start_line, start_col)
                escaped = self._advance()
                if escaped == "n":
                    chars.append("\n")
                elif escaped == "t":
                    chars.append("\t")
                elif escaped == '"':
                    chars.append('"')
                elif escaped == "\\":
                    chars.append("\\")
                else:
                    chars.append(escaped)
            else:
                chars.append(self._advance())
        return Token(STRING, "".join(chars), start_line, start_col)

    def _read_number(self):
        start_line = self.line
        start_col = self.column
        digits = []
        while self._peek() is not None and self._peek().isdigit():
            digits.append(self._advance())
        val = int("".join(digits))
        return Token(NUMBER, val, start_line, start_col)

    def _read_identifier_or_keyword(self):
        start_line = self.line
        start_col = self.column
        chars = []
        while self._peek() is not None and (self._peek().isalnum() or self._peek() == "_"):
            chars.append(self._advance())
        word = "".join(chars)
        if word in KEYWORDS:
            return Token(word, word, start_line, start_col)
        elif word == "true":
            return Token(BOOL, True, start_line, start_col)
        elif word == "false":
            return Token(BOOL, False, start_line, start_col)
        else:
            return Token(IDENT, word, start_line, start_col)

    def next_token(self):
        self._skip_whitespace_and_comments()
        if self.pos >= self.length:
            return Token(EOF, None, self.line, self.column)

        ch = self._peek()
        start_line = self.line
        start_col = self.column

        if ch == '"':
            return self._read_string()

        if ch.isdigit():
            return self._read_number()

        if ch.isalpha() or ch == "_":
            return self._read_identifier_or_keyword()

        next_ch = self._peek(1)
        if next_ch is not None:
            two_chars = ch + next_ch
            if two_chars in TWO_CHAR_TOKENS:
                self._advance()
                self._advance()
                return Token(TWO_CHAR_TOKENS[two_chars], two_chars, start_line, start_col)

        if ch in SINGLE_CHAR_TOKENS:
            self._advance()
            return Token(SINGLE_CHAR_TOKENS[ch], ch, start_line, start_col)

        self._advance()
        raise LexError(f"Neočekivan karakter: {ch!r}", start_line, start_col)

    def tokenize(self):
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == EOF:
                break
        return tokens
