class AdventureError(Exception):
    """Osnovna klasa za sve greške."""
    kind = "Greška"

    def __init__(self, message, line, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(message)

    def __str__(self):
        where = f"linija {self.line}"
        if(self.column) is not None:
            where+=f", kolona {self.column}"
        return f"{self.kind} ({where}): {self.message}"

class LexError(AdventureError):
    kind = "Leksička greška"


class ParseError(AdventureError):
    kind = "Sintaksna greška"


class SemanticError(AdventureError):
    kind = "Semantička greška"