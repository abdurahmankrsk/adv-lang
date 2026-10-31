from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


@dataclass
class ASTNode:
    line: int = 0
    column: int = 0


@dataclass
class Program(ASTNode):
    story: str = ""
    start_location: str = ""
    items: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    initial_state: Dict[str, Any] = field(default_factory=dict)
    locations: List["Location"] = field(default_factory=list)


@dataclass
class Location(ASTNode):
    name: str = ""
    statements: List["Statement"] = field(default_factory=list)
    options: List["Option"] = field(default_factory=list)


@dataclass
class Option(ASTNode):
    key: str = ""
    text: str = ""
    condition: Optional["Expression"] = None
    hint: Optional[str] = None
    body: List["Statement"] = field(default_factory=list)


@dataclass
class Statement(ASTNode):
    pass


@dataclass
class TextStmt(Statement):
    message: str = ""


@dataclass
class SetStmt(Statement):
    variable: str = ""
    value: "Expression" = None


@dataclass
class AddItemStmt(Statement):
    item: str = ""


@dataclass
class RemoveItemStmt(Statement):
    item: str = ""


@dataclass
class GotoStmt(Statement):
    target: str = ""


@dataclass
class EndStmt(Statement):
    message: str = ""


@dataclass
class IfStmt(Statement):
    condition: "Expression" = None
    then_branch: List[Statement] = field(default_factory=list)
    else_branch: List[Statement] = field(default_factory=list)


@dataclass
class WhileStmt(Statement):
    condition: "Expression" = None
    body: List[Statement] = field(default_factory=list)


@dataclass
class Expression(ASTNode):
    pass


@dataclass
class LiteralExpr(Expression):
    value: Any = None


@dataclass
class VarExpr(Expression):
    name: str = ""


@dataclass
class HasExpr(Expression):
    item: str = ""


@dataclass
class UnaryExpr(Expression):
    op: str = ""
    operand: Expression = None


@dataclass
class BinaryExpr(Expression):
    left: Expression = None
    op: str = ""
    right: Expression = None
