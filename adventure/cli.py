import sys
import os
import argparse
import unittest

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from adventure.semantic import SemanticAnalyzer
    from adventure.interpreter import Interpreter
    from adventure.codegen import HTMLCodeGenerator
    from adventure.errors import AdventureError
except ImportError:
    from semantic import SemanticAnalyzer
    from interpreter import Interpreter
    from codegen import HTMLCodeGenerator
    from errors import AdventureError


def cmd_check(args):
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
        analyzer = SemanticAnalyzer(code)
        ast = analyzer.analyze()
        print(f"[OK] Fajl '{args.file}' je uspesno verifikovan.")
        print(f"     Naslov: '{ast.story}'")
        print(f"     Broj lokacija: {len(ast.locations)}")
        print(f"     Pocetna lokacija: '{ast.start_location}'")
        return 0
    except AdventureError as e:
        print(f"[GRESKA] {e}")
        return 1
    except FileNotFoundError:
        print(f"[GRESKA] Fajl '{args.file}' nije pronadjen.")
        return 1


def cmd_play(args):
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
        interp = Interpreter(code)
        interp.run()
        return 0
    except AdventureError as e:
        print(f"[GRESKA] {e}")
        return 1
    except FileNotFoundError:
        print(f"[GRESKA] Fajl '{args.file}' nije pronadjen.")
        return 1


def cmd_export(args):
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
        gen = HTMLCodeGenerator(code)
        html = gen.generate()
        out_path = args.output
        if not out_path:
            base_name = os.path.splitext(os.path.basename(args.file))[0]
            out_path = f"{base_name}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] Igra je uspesno eksportovana u web format: '{out_path}'")
        return 0
    except AdventureError as e:
        print(f"[GRESKA] {e}")
        return 1
    except FileNotFoundError:
        print(f"[GRESKA] Fajl '{args.file}' nije pronadjen.")
        return 1


def cmd_test(args):
    tests_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "tests")
    )
    suite = unittest.defaultTestLoader.discover(tests_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(
        prog="adventure",
        description="Adventure DSL - Prevodilac, interpreter i generator interaktivnih avantura",
    )
    subparsers = parser.add_subparsers(dest="command", help="Dostupne komande")

    check_parser = subparsers.add_parser("check", help="Provera sintakse i semantike .adv fajla")
    check_parser.add_argument("file", help="Putanja do .adv fajla")

    play_parser = subparsers.add_parser("play", help="Direktno igranje avanture u konzoli")
    play_parser.add_argument("file", help="Putanja do .adv fajla")

    export_parser = subparsers.add_parser("export", help="Prevodjenje .adv avanture u HTML/JS igru")
    export_parser.add_argument("file", help="Putanja do .adv fajla")
    export_parser.add_argument("-o", "--output", help="Naziv izlaznog HTML fajla")

    subparsers.add_parser("test", help="Pokretanje svih automatskih testova prevodioca")

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check(args))
    elif args.command == "play":
        sys.exit(cmd_play(args))
    elif args.command == "export":
        sys.exit(cmd_export(args))
    elif args.command == "test":
        sys.exit(cmd_test(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
