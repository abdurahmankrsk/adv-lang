# Adventure DSL

**Adventure DSL** je deklarativni domenski specifičan jezik za pisanje i pokretanje tekstualnih avantura i interaktivne fikcije, razvijen u okviru predmeta **Programski prevodioci** na **Računarskom fakultetu (RAF)**.

- **Studenti:** Boris Mirković, Abdurahman Karišik
- **Saradnik u nastavi:** Mihajlo Stojanović (`m_stojanovic@raf.rs`)

---

##  Osobine i arhitektura prevodioca

Prevodilac je implementiran u čistom programskom jeziku **Python (3.10+)** bez spoljnih zavisnosti. Obuhvata sve analitičke i generičke faze prevođenja:

1. **Leksička analiza (`adventure/lexer.py`)**
   - Pretvaranje koda u tok tokena uz praćenje linija i kolona.
   - Podrška za ključne reči, brojeve, stringove, lokalizovana latinična slova (`č, ć, ž, š, đ`), operatore i jednolinijske komentare (`#`).
2. **Sintaksna analiza (`adventure/parser.py`, `adventure/ast.py`)**
   - Rekurzivni silazni parser (Recursive Descent) zasnovan na formalnoj LL(1) EBNF gramatici bez leve rekurzije.
   - Hijerarhija sa 8 nivoa prioriteta operatora (`OR`, `AND`, `==/!=`, poređenja, `+/-`, `*/\/`, unarni `NOT/-`, primarni izrazi).
3. **Semantička analiza (`adventure/semantic.py`)**
   - Tabela simbola i automatsko izvođenje tipova (*Type Inference*) iz početnog stanja.
   - Statička verifikacija dosega: postojanje početne lokacije, jedinstvenost imena lokacija i opcija, validnost `GOTO` prelaza, deklarisanost predmeta i promenljivih, provera tipova u `SET` i logičkih uslova u `IF` i `WHILE`.
4. **Generička faza 1: Konzolni Interpreter (`adventure/interpreter.py`)**
   - Direktno obilazi i izvršava AST stablo u terminalu.
   - Upravljanje promenljivim stanja, inventarom, dinamičkim otključavanjem opcija i prikazom saveta (`HINT`).
5. **Generička faza 2: Web Transpajler (`adventure/codegen.py`)**
   - Prevođenje `.adv` koda u samostalnu, modernu veb igru u formatu HTML5 i JavaScript.
   - Generisani fajl (12–14 KB) radi u bilo kom pretraživaču na računaru ili telefonu bez instaliranja softvera ili servera.

---

##  Pokretanje i upotreba (CLI)

Prevodilac poseduje integrisani komandno-linijski interfejs:

### 1. Provera sintaksne i semantičke ispravnosti
```bash
python -m adventure check examples/01_tvrdjava.adv
```

### 2. Igranje avanture u konzoli
```bash
python -m adventure play examples/01_tvrdjava.adv
```

### 3. Prevođenje u samostalnu web igricu
```bash
python -m adventure export examples/01_tvrdjava.adv -o igra.html
```
*Nakon ovoga, samo otvorite `igra.html` u bilo kom pretraživaču.*

### 4. Pokretanje svih automatskih testova
```bash
python -m adventure test
```

---

##  Struktura repozitorijuma

```text
Projekat/
├── adventure/               # Izvorni kod prevodioca
│   ├── ast.py               # Čvorovi apstraktnog sintaksnog stabla
│   ├── cli.py               # Komandno-linijski interfejs
│   ├── codegen.py           # Generator HTML/JS koda
│   ├── errors.py            # Hijerarhija grešaka (Lex, Parse, Semantic)
│   ├── interpreter.py       # Konzolni interpreter
│   ├── lexer.py             # Leksički analizator
│   ├── parser.py            # Rekurzivni silazni parser
│   ├── semantic.py          # Semantički analizator i provera tipova
│   ├── tokens.py            # Definicije tokena i ključnih reči
│   ├── __init__.py          # Export modula
│   └── __main__.py          # Ulazna tačka za 'python -m adventure'
├── docs/                    # Dokumentacija
│   ├── abstract.md          # Preliminarni apstrakt rada
│   └── grammar.md           # Formalna specifikacija EBNF gramatike
├── examples/                # 10 testnih i demonstracionih priča (.adv)
│   ├── 01_tvrdjava.adv
│   ├── 02_pecina.adv
│   ├── ...
│   └── 10_svetionik.adv
├── paper/                   # Mali naučni rad prema šablonu
│   ├── arhitektura.png      # Ilustracija 1 (dijagram arhitekture)
│   ├── rad.docx             # Rad u Microsoft Word formatu
│   └── rad.tex              # Rad u LaTeX formatu
├── tests/                   # Automatizovani testovi
│   ├── __init__.py
│   └── test_all.py          # 17 jediničnih i integracionih testova
└── README.md                # Dokumentacija projekta
```

---

##  Verifikacija i testovi

Test paket (`tests/test_all.py`) pokriva celokupan pajplajn prevodioca:
- Lekser (prepoznavanje leksema, escape sekvence, nezatvoreni stringovi, nedozvoljeni karakteri).
- Parser (građenje AST-a, prioritet operatora, sintaksne greške).
- Semantička analiza (tabela simbola, provera tipova, hvatanje nepostojećih skokova i nedeklarisanih promenljivih).
- Interpreter (simulacija avanture sa mock unosom, `WHILE` petlje, manipulacija inventarom).
- Generator koda (validnost generisanog HTML5/JS koda).
- Integracioni test koji automatski verifikuje svih 10 priča u folderu `examples/`.
