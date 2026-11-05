import unittest
import glob
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adventure import (
    Lexer,
    Parser,
    SemanticAnalyzer,
    Interpreter,
    HTMLCodeGenerator,
    LexError,
    ParseError,
    SemanticError,
    BinaryExpr,
    LiteralExpr,
    VarExpr,
)


class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        source = 'STORY "Naslov" START_LOCATION pocetak ITEMS [mac] INVENTORY [] STATE { zivot = 100, aktivan = true }'
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens]
        self.assertIn("STORY", types)
        self.assertIn("STRING", types)
        self.assertIn("START_LOCATION", types)
        self.assertIn("IDENT", types)
        self.assertIn("ITEMS", types)
        self.assertIn("NUMBER", types)
        self.assertIn("BOOL", types)
        self.assertEqual(types[-1], "EOF")

    def test_operators_and_punctuation(self):
        source = "== != <= >= < > + - * / { } [ ] ( ) , ="
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != "EOF"]
        expected = [
            "EQ", "NEQ", "LE", "GE", "LT", "GT",
            "PLUS", "MINUS", "STAR", "SLASH",
            "LBRACE", "RBRACE", "LBRACKET", "RBRACKET",
            "LPAREN", "RPAREN", "COMMA", "ASSIGN",
        ]
        self.assertEqual(types, expected)

    def test_unclosed_string_raises_error(self):
        source = 'STORY "Ovo nije zatvoreno'
        with self.assertRaises(LexError):
            Lexer(source).tokenize()

    def test_unexpected_char_raises_error(self):
        source = "LOCATION $soba {}"
        with self.assertRaises(LexError):
            Lexer(source).tokenize()


class TestParser(unittest.TestCase):
    def test_parse_minimal_valid_program(self):
        source = """STORY "Test"
START_LOCATION pocetak
ITEMS []
INVENTORY []
STATE {}
LOCATION pocetak {
    TEXT "Zdravo svete"
    END "Kraj"
}"""
        ast = Parser(source).parse()
        self.assertEqual(ast.story, "Test")
        self.assertEqual(ast.start_location, "pocetak")
        self.assertEqual(len(ast.locations), 1)
        self.assertEqual(ast.locations[0].name, "pocetak")
        self.assertEqual(len(ast.locations[0].statements), 2)

    def test_operator_precedence(self):
        source = """STORY "Test"
START_LOCATION pocetak
ITEMS []
INVENTORY []
STATE { rez = 0 }
LOCATION pocetak {
    SET rez = 1 + 2 * 3
}"""
        ast = Parser(source).parse()
        stmt = ast.locations[0].statements[0]
        expr = stmt.value
        self.assertIsInstance(expr, BinaryExpr)
        self.assertEqual(expr.op, "+")
        self.assertIsInstance(expr.left, LiteralExpr)
        self.assertEqual(expr.left.value, 1)
        self.assertIsInstance(expr.right, BinaryExpr)
        self.assertEqual(expr.right.op, "*")

    def test_syntax_error_missing_location_brace(self):
        source = """STORY "Test"
START_LOCATION pocetak
ITEMS []
INVENTORY []
STATE {}
LOCATION pocetak
    TEXT "Nema zagrade"
}"""
        with self.assertRaises(ParseError):
            Parser(source).parse()


class TestSemanticAnalyzer(unittest.TestCase):
    def test_valid_semantic_program(self):
        source = """STORY "Test"
START_LOCATION a
ITEMS [kljuc]
INVENTORY [kljuc]
STATE { brojac = 0 }
LOCATION a {
    IF HAS kljuc {
        SET brojac = brojac + 1
        GOTO b
    }
}
LOCATION b {
    END "Gotovo"
}"""
        ast = SemanticAnalyzer(source).analyze()
        self.assertIsNotNone(ast)

    def test_undefined_start_location(self):
        source = """STORY "Test"
START_LOCATION nepostojeca
ITEMS []
INVENTORY []
STATE {}
LOCATION soba {
    END "Kraj"
}"""
        with self.assertRaises(SemanticError):
            SemanticAnalyzer(source).analyze()

    def test_undefined_goto_target(self):
        source = """STORY "Test"
START_LOCATION soba
ITEMS []
INVENTORY []
STATE {}
LOCATION soba {
    GOTO nepostojeca
}"""
        with self.assertRaises(SemanticError):
            SemanticAnalyzer(source).analyze()

    def test_undeclared_item_in_inventory(self):
        source = """STORY "Test"
START_LOCATION soba
ITEMS []
INVENTORY [kljuc]
STATE {}
LOCATION soba {
    END "Kraj"
}"""
        with self.assertRaises(SemanticError):
            SemanticAnalyzer(source).analyze()

    def test_type_mismatch_in_set(self):
        source = """STORY "Test"
START_LOCATION soba
ITEMS []
INVENTORY []
STATE { broj = 5 }
LOCATION soba {
    SET broj = "nije broj"
}"""
        with self.assertRaises(SemanticError):
            SemanticAnalyzer(source).analyze()

    def test_non_bool_condition_in_if(self):
        source = """STORY "Test"
START_LOCATION soba
ITEMS []
INVENTORY []
STATE { broj = 5 }
LOCATION soba {
    IF broj + 1 {
        TEXT "Greska"
    }
}"""
        with self.assertRaises(SemanticError):
            SemanticAnalyzer(source).analyze()


class TestInterpreter(unittest.TestCase):
    def test_interpreter_simulation(self):
        source = """STORY "Simulacija"
START_LOCATION soba1
ITEMS [novcic]
INVENTORY []
STATE { koraci = 0 }

LOCATION soba1 {
    OPTION a "Uzmi novcic" IF NOT HAS novcic {
        ADD_ITEM novcic
        SET koraci = koraci + 1
        GOTO soba2
    }
}

LOCATION soba2 {
    IF HAS novcic {
        END "Pobedio si sa novcicem!"
    } ELSE {
        END "Izgubio si!"
    }
}"""
        inputs = ["a"]
        outputs = []
        interp = Interpreter(
            source,
            input_fn=lambda prompt: inputs.pop(0),
            output_fn=lambda msg: outputs.append(str(msg)),
        )
        interp.run()

        self.assertTrue(interp.is_ended)
        self.assertIn("novcic", interp.inventory)
        self.assertEqual(interp.state["koraci"], 1)
        self.assertTrue(any("Pobedio si sa novcicem!" in out for out in outputs))

    def test_interpreter_while_loop(self):
        source = """STORY "Petlja"
START_LOCATION start
ITEMS []
INVENTORY []
STATE { brojac = 3 }

LOCATION start {
    WHILE brojac > 0 {
        SET brojac = brojac - 1
    }
    END "Brojac je nula"
}"""
        interp = Interpreter(source, output_fn=lambda m: None)
        interp.run()
        self.assertEqual(interp.state["brojac"], 0)
        self.assertTrue(interp.is_ended)


class TestCodeGen(unittest.TestCase):
    def test_html_generation(self):
        source = """STORY "WebTest"
START_LOCATION pocetak
ITEMS [kamen]
INVENTORY [kamen]
STATE { zivot = 10 }
LOCATION pocetak {
    TEXT "Nalazis se na webu."
    END "Kraj"
}"""
        gen = HTMLCodeGenerator(source)
        html = gen.generate()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("WebTest", html)
        self.assertIn("const locations =", html)
        self.assertIn("pocetak", html)
        self.assertIn("kamen", html)


class TestAllExamples(unittest.TestCase):
    def test_all_ten_examples_pipeline(self):
        examples_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "examples")
        )
        adv_files = sorted(glob.glob(os.path.join(examples_dir, "*.adv")))
        self.assertGreaterEqual(len(adv_files), 10)

        for adv_path in adv_files:
            with open(adv_path, "r", encoding="utf-8") as f:
                content = f.read()

            tokens = Lexer(content).tokenize()
            self.assertGreater(len(tokens), 0)

            ast = Parser(tokens).parse()
            self.assertIsNotNone(ast.story)

            checked_ast = SemanticAnalyzer(ast).analyze()
            self.assertIsNotNone(checked_ast)

            html = HTMLCodeGenerator(checked_ast).generate()
            self.assertIn("<!DOCTYPE html>", html)


if __name__ == "__main__":
    unittest.main()
