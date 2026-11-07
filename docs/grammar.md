# Formalna gramatika jezika Adventure DSL (EBNF)

Ovaj dokument definiše leksičku i sintaksnu strukturu domenskog jezika **Adventure DSL** korišćenjem Proširene Bakus-Nurove forme (EBNF - *Extended Backus-Naur Form*).

---

## 1. Leksička gramatika (Terminali)

Lekser pretvara izvorni tekst u tokene ignorišući beline (` `, `\t`, `\r`, `\n`) i komentare koji počinju znakom `#` i traju do kraja linije.

### Ključne reči (Keywords)
```ebnf
KEYWORD ::= "STORY" | "START_LOCATION" | "ITEMS" | "INVENTORY" | "STATE"
          | "LOCATION" | "TEXT" | "OPTION" | "HINT"
          | "IF" | "ELSE" | "WHILE"
          | "HAS" | "NOT" | "AND" | "OR"
          | "ADD_ITEM" | "REMOVE_ITEM" | "SET" | "GOTO" | "END"
```

### Literali i identifikatori
```ebnf
LETTER      ::= "a" ... "z" | "A" ... "Z" | "č" | "ć" | "ž" | "š" | "đ" | "Č" | "Ć" | "Ž" | "Š" | "Đ" | "_"
DIGIT       ::= "0" ... "9"
IDENT       ::= LETTER ( LETTER | DIGIT )*   (* osim ključnih reči *)
NUMBER      ::= DIGIT+
BOOL        ::= "true" | "false"
STRING      ::= '"' ( [^"\] | '\' [nt"\\] )* '"'
```

### Operatori i separatori
```ebnf
ASSIGN      ::= "="
EQ          ::= "=="
NEQ         ::= "!="
LT          ::= "<"
LE          ::= "<="
GT          ::= ">"
GE          ::= ">="
PLUS        ::= "+"
MINUS       ::= "-"
STAR        ::= "*"
SLASH       ::= "/"
LBRACE      ::= "{"
RBRACE      ::= "}"
LBRACKET    ::= "["
RBRACKET    ::= "]"
LPAREN      ::= "("
RPAREN      ::= ")"
COMMA       ::= ","
```

---

## 2. Sintaksna gramatika (Neterminali)

### Struktura programa i zaglavlja
```ebnf
Program         ::= Header Location+ EOF

Header          ::= StoryDecl StartLocDecl ItemsDecl InvDecl StateDecl

StoryDecl       ::= "STORY" STRING
StartLocDecl    ::= "START_LOCATION" IDENT
ItemsDecl       ::= "ITEMS" "[" [ IDENT ( "," IDENT )* ] "]"
InvDecl         ::= "INVENTORY" "[" [ IDENT ( "," IDENT )* ] "]"
StateDecl       ::= "STATE" "{" [ VarInit ( "," VarInit )* ] "}"

VarInit         ::= IDENT "=" StateValue
StateValue      ::= NUMBER | STRING | BOOL | "-" NUMBER
```

### Lokacije i opcije
```ebnf
Location        ::= "LOCATION" IDENT "{" ( Statement | Option )* "}"

Option          ::= "OPTION" IDENT STRING [ OptionCond ] [ OptionHint ] "{" Statement* "}"
OptionCond      ::= "IF" Expression
OptionHint      ::= "HINT" STRING
```

### Naredbe (Statements)
```ebnf
Statement       ::= TextStmt
                  | SetStmt
                  | AddItemStmt
                  | RemoveItemStmt
                  | GotoStmt
                  | EndStmt
                  | IfStmt
                  | WhileStmt

TextStmt        ::= "TEXT" STRING
SetStmt         ::= "SET" IDENT "=" Expression
AddItemStmt     ::= "ADD_ITEM" IDENT
RemoveItemStmt  ::= "REMOVE_ITEM" IDENT
GotoStmt        ::= "GOTO" IDENT
EndStmt         ::= "END" STRING
IfStmt          ::= "IF" Expression "{" Statement* "}" [ "ELSE" "{" Statement* "}" ]
WhileStmt       ::= "WHILE" Expression "{" Statement* "}"
```

### Izrazi i hijerarhija prioriteta operatora
Izrazi su organizovani hijerarhijski kako bi se osigurao ispravan prioritet bez leve rekurzije:

```ebnf
Expression      ::= OrExpr
OrExpr          ::= AndExpr ( "OR" AndExpr )*
AndExpr         ::= EqExpr ( "AND" EqExpr )*
EqExpr          ::= CompExpr ( ( "==" | "!=" ) CompExpr )*
CompExpr        ::= TermExpr ( ( "<" | "<=" | ">" | ">=" ) TermExpr )*
TermExpr        ::= FactorExpr ( ( "+" | "-" ) FactorExpr )*
FactorExpr      ::= UnaryExpr ( ( "*" | "/" ) UnaryExpr )*
UnaryExpr       ::= ( "NOT" | "-" ) UnaryExpr | PrimaryExpr
PrimaryExpr     ::= "HAS" IDENT
                  | NUMBER
                  | STRING
                  | BOOL
                  | IDENT
                  | "(" Expression ")"
```

---

## 3. Tabela prioriteta operatora

| Nivo | Operator | Opis | Asocijativnost |
| :---: | :--- | :--- | :---: |
| 1 (najviši) | `( )`, Literali, `IDENT`, `HAS` | Primarni izrazi i pozivi | N/A |
| 2 | `NOT`, unarni `-` | Unarna negacija i promena znaka | Zdesna nalevo |
| 3 | `*`, `/` | Množenje i celobrojno deljenje | Sleva nadesno |
| 4 | `+`, `-` | Sabiranje i oduzimanje | Sleva nadesno |
| 5 | `<`, `<=`, `>`, `>=` | Relaciona poređenja | Sleva nadesno |
| 6 | `==`, `!=` | Jednakost i nejednakost | Sleva nadesno |
| 7 | `AND` | Logičko I | Sleva nadesno |
| 8 (najniži) | `OR` | Logičko ILI | Sleva nadesno |
