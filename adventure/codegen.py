import sys
import json

try:
    from adventure.semantic import SemanticAnalyzer
    from adventure.ast import (
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
    from semantic import SemanticAnalyzer
    from ast import (
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


class HTMLCodeGenerator:
    def __init__(self, program_or_source):
        if isinstance(program_or_source, str):
            self.program = SemanticAnalyzer(program_or_source).analyze()
        else:
            self.program = program_or_source

    def _emit_expr(self, expr):
        if isinstance(expr, LiteralExpr):
            return json.dumps(expr.value)

        if isinstance(expr, VarExpr):
            return f"state[{json.dumps(expr.name)}]"

        if isinstance(expr, HasExpr):
            return f"inventory.includes({json.dumps(expr.item)})"

        if isinstance(expr, UnaryExpr):
            inner = self._emit_expr(expr.operand)
            if expr.op == "NOT":
                return f"(!({inner}))"
            if expr.op == "-":
                return f"(-({inner}))"

        if isinstance(expr, BinaryExpr):
            left = self._emit_expr(expr.left)
            right = self._emit_expr(expr.right)
            op = expr.op
            if op == "AND":
                return f"({left} && {right})"
            if op == "OR":
                return f"({left} || {right})"
            if op == "==":
                return f"({left} === {right})"
            if op == "!=":
                return f"({left} !== {right})"
            if op == "/":
                return f"Math.floor({left} / {right})"
            return f"({left} {op} {right})"

        return "null"

    def _emit_statements(self, statements, indent=12):
        ind = " " * indent
        lines = []
        for stmt in statements:
            if isinstance(stmt, TextStmt):
                lines.append(f"{ind}addText({json.dumps(stmt.message)});")
            elif isinstance(stmt, EndStmt):
                lines.append(f"{ind}endGame({json.dumps(stmt.message)});")
                lines.append(f"{ind}return;")
            elif isinstance(stmt, GotoStmt):
                lines.append(f"{ind}goToLocation({json.dumps(stmt.target)});")
                lines.append(f"{ind}return;")
            elif isinstance(stmt, SetStmt):
                lines.append(f"{ind}state[{json.dumps(stmt.variable)}] = {self._emit_expr(stmt.value)};")
                lines.append(f"{ind}updateStatus();")
            elif isinstance(stmt, AddItemStmt):
                lines.append(f"{ind}addItem({json.dumps(stmt.item)});")
            elif isinstance(stmt, RemoveItemStmt):
                lines.append(f"{ind}removeItem({json.dumps(stmt.item)});")
            elif isinstance(stmt, IfStmt):
                cond = self._emit_expr(stmt.condition)
                lines.append(f"{ind}if ({cond}) {{")
                lines.append(self._emit_statements(stmt.then_branch, indent + 4))
                if stmt.else_branch:
                    lines.append(f"{ind}}} else {{")
                    lines.append(self._emit_statements(stmt.else_branch, indent + 4))
                lines.append(f"{ind}}}")
            elif isinstance(stmt, WhileStmt):
                cond = self._emit_expr(stmt.condition)
                lines.append(f"{ind}while ({cond}) {{")
                lines.append(self._emit_statements(stmt.body, indent + 4))
                lines.append(f"{ind}}}")
        return "\n".join(lines)

    def _emit_locations_js(self):
        chunks = []
        for loc in self.program.locations:
            options_chunks = []
            for opt in loc.options:
                cond_code = self._emit_expr(opt.condition) if opt.condition else "true"
                hint_code = json.dumps(opt.hint) if opt.hint else "null"
                body_code = self._emit_statements(opt.body, 20)
                opt_chunk = f"""                {{
                    key: {json.dumps(opt.key)},
                    text: {json.dumps(opt.text)},
                    isAvailable: function() {{ return {cond_code}; }},
                    hint: {hint_code},
                    execute: function() {{
{body_code}
                    }}
                }}"""
                options_chunks.append(opt_chunk)

            options_str = ",\n".join(options_chunks)
            enter_body = self._emit_statements(loc.statements, 16)
            loc_chunk = f"""        {json.dumps(loc.name)}: {{
            name: {json.dumps(loc.name)},
            enter: function() {{
{enter_body}
            }},
            options: [
{options_str}
            ]
        }}"""
            chunks.append(loc_chunk)
        return ",\n".join(chunks)

    def generate(self):
        story_json = json.dumps(self.program.story)
        start_loc_json = json.dumps(self.program.start_location)
        initial_inv_json = json.dumps(self.program.inventory)
        initial_state_json = json.dumps(self.program.initial_state)
        locations_js = self._emit_locations_js()

        return f"""<!DOCTYPE html>
<html lang="sr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.program.story}</title>
    <style>
        :root {{
            --bg-main: #121418;
            --bg-card: #1c2026;
            --bg-button: #2a313c;
            --bg-button-hover: #3d4757;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent: #60a5fa;
            --accent-glow: rgba(96, 165, 250, 0.2);
            --danger: #f87171;
            --border: #334155;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px;
        }}
        .game-container {{
            width: 100%;
            max-width: 780px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        .header {{
            background: rgba(15, 23, 42, 0.6);
            padding: 20px 28px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            font-size: 1.4rem;
            color: var(--accent);
            letter-spacing: 0.5px;
        }}
        .status-bar {{
            padding: 12px 28px;
            background: rgba(15, 23, 42, 0.3);
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            color: var(--text-muted);
        }}
        .status-item strong {{
            color: var(--text-main);
        }}
        .badge {{
            display: inline-block;
            background: #2563eb;
            color: #fff;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-right: 4px;
        }}
        .story-area {{
            padding: 28px;
            min-height: 240px;
            max-height: 380px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            line-height: 1.6;
            font-size: 1.05rem;
        }}
        .story-para {{
            animation: fadeIn 0.3s ease;
        }}
        .options-area {{
            padding: 20px 28px 28px 28px;
            border-top: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .opt-btn {{
            background: var(--bg-button);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .opt-btn:hover:not(:disabled) {{
            background: var(--bg-button-hover);
            border-color: var(--accent);
            box-shadow: 0 0 12px var(--accent-glow);
            transform: translateY(-1px);
        }}
        .opt-btn:disabled {{
            opacity: 0.45;
            cursor: not-allowed;
            border-style: dashed;
        }}
        .opt-key {{
            background: var(--bg-main);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.9rem;
            border: 1px solid var(--border);
        }}
        .hint-text {{
            font-size: 0.85rem;
            color: var(--danger);
            margin-left: auto;
        }}
        .restart-btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            margin-top: 10px;
            align-self: flex-start;
        }}
        .restart-btn:hover {{
            background: #1d4ed8;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="game-container">
        <div class="header">
            <h1 id="story-title">{self.program.story}</h1>
            <span id="loc-badge" class="badge" style="background: #475569;">Lokacija: -</span>
        </div>
        <div class="status-bar">
            <div class="status-item">Inventar: <span id="inv-display">Prazan</span></div>
            <div class="status-item">Stanje: <span id="state-display">-</span></div>
        </div>
        <div class="story-area" id="story-log"></div>
        <div class="options-area" id="options-box"></div>
    </div>

    <script>
        const initialInventory = {initial_inv_json};
        const initialState = {initial_state_json};
        const startLocationName = {start_loc_json};

        let inventory = [...initialInventory];
        let state = {{ ...initialState }};
        let currentLocation = startLocationName;
        let isEnded = false;

        const storyLog = document.getElementById("story-log");
        const optionsBox = document.getElementById("options-box");
        const invDisplay = document.getElementById("inv-display");
        const stateDisplay = document.getElementById("state-display");
        const locBadge = document.getElementById("loc-badge");

        const locations = {{
{locations_js}
        }};

        function addText(msg) {{
            const p = document.createElement("p");
            p.className = "story-para";
            p.textContent = msg;
            storyLog.appendChild(p);
            storyLog.scrollTop = storyLog.scrollHeight;
        }}

        function addItem(item) {{
            if (!inventory.includes(item)) {{
                inventory.push(item);
                updateStatus();
            }}
        }}

        function removeItem(item) {{
            const idx = inventory.indexOf(item);
            if (idx !== -1) {{
                inventory.splice(idx, 1);
                updateStatus();
            }}
        }}

        function goToLocation(target) {{
            currentLocation = target;
            updateStatus();
            enterLocation();
        }}

        function endGame(msg) {{
            isEnded = true;
            addText(msg);
            renderOptions();
        }}

        function updateStatus() {{
            locBadge.textContent = "Lokacija: " + currentLocation;
            if (inventory.length === 0) {{
                invDisplay.textContent = "Prazan";
            }} else {{
                invDisplay.innerHTML = inventory.map(i => '<span class="badge">' + i + '</span>').join(" ");
            }}
            const stateEntries = Object.entries(state);
            if (stateEntries.length === 0) {{
                stateDisplay.textContent = "-";
            }} else {{
                stateDisplay.textContent = stateEntries.map(([k, v]) => k + ": " + v).join(", ");
            }}
        }}

        function enterLocation() {{
            const loc = locations[currentLocation];
            if (!loc) return;
            loc.enter();
            if (!isEnded) {{
                renderOptions();
            }}
        }}

        function renderOptions() {{
            optionsBox.innerHTML = "";
            if (isEnded) {{
                const btn = document.createElement("button");
                btn.className = "restart-btn";
                btn.textContent = "Igraj ponovo";
                btn.onclick = restartGame;
                optionsBox.appendChild(btn);
                return;
            }}

            const loc = locations[currentLocation];
            if (!loc || !loc.options || loc.options.length === 0) return;

            for (const opt of loc.options) {{
                const available = opt.isAvailable();
                const btn = document.createElement("button");
                btn.className = "opt-btn";
                btn.disabled = !available;

                const keySpan = document.createElement("span");
                keySpan.className = "opt-key";
                keySpan.textContent = opt.key.toUpperCase();
                btn.appendChild(keySpan);

                const textSpan = document.createElement("span");
                textSpan.textContent = opt.text;
                btn.appendChild(textSpan);

                if (!available && opt.hint) {{
                    const hintSpan = document.createElement("span");
                    hintSpan.className = "hint-text";
                    hintSpan.textContent = opt.hint;
                    btn.appendChild(hintSpan);
                }}

                if (available) {{
                    btn.onclick = function() {{
                        opt.execute();
                    }};
                }}

                optionsBox.appendChild(btn);
            }}
        }}

        function restartGame() {{
            inventory = [...initialInventory];
            state = {{ ...initialState }};
            currentLocation = startLocationName;
            isEnded = false;
            storyLog.innerHTML = "";
            updateStatus();
            enterLocation();
        }}

        window.onload = function() {{
            updateStatus();
            enterLocation();
        }};
    </script>
</body>
</html>"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        src_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "index.html"
        with open(src_path, "r", encoding="utf-8") as f:
            code = f.read()
        generator = HTMLCodeGenerator(code)
        html = generator.generate()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Igra uspesno prevedena u web format: {out_path}")
    else:
        print("Upotreba: python -m adventure.codegen <putanja_do_adv_fajla> [izlazni_html_fajl]")
