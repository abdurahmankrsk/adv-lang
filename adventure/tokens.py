KEYWORDS = {
    "STORY", "START_LOCATION", "ITEMS", "INVENTORY", "STATE",
    "LOCATION", "TEXT", "OPTION", "HINT",
    "IF", "ELSE", "WHILE",
    "HAS", "NOT", "AND", "OR",
    "ADD_ITEM", "REMOVE_ITEM", "SET", "GOTO", "END",
}

IDENT = "IDENT"
NUMBER = "NUMBER"
STRING = "STRING"
BOOL = "BOOL"
EOF = "EOF"

SINGLE_CHAR_TOKENS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    "=": "ASSIGN",
    "<": "LT",
    ">": "GT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
}

TWO_CHAR_TOKENS = {
    "==": "EQ",
    "!=": "NEQ",
    "<=": "LE",
    ">=": "GE",
}

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"