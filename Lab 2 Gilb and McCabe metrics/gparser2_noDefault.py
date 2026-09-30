import tkinter as tk
from tkinter import filedialog, messagebox, ttk

GO_KEYWORDS = {
    "break", "default", "func", "interface", "select", "case", "defer",
    "go", "map", "struct", "chan", "else", "goto", "package", "switch",
    "const", "fallthrough", "if", "range", "type", "continue", "for",
    "import", "return", "var",
}

OPERATORS = {
    "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=",
    "&&", "||", "!", "&", "|", "^", "<<", ">>", "&^",
    "=", ":=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
    "<<=", ">>=", "&^=", "++", "--", ".", ",", ";", ":", "...",
    "<-",
}

MULTI_OPERATORS = sorted(OPERATORS, key=len, reverse=True)

def lex_go(source):
    """Лексер Go-кода."""
    tokens = []
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        if ch.isspace():
            i += 1
            continue

        if source.startswith("//", i):
            end = source.find("\n", i)
            i = n if end == -1 else end
            continue

        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue

        if ch in ('"', "'", "`"):
            quote = ch
            start = i
            i += 1
            while i < n:
                if quote != "`" and source[i] == "\\":
                    i += 2
                    continue
                if source[i] == quote:
                    i += 1
                    break
                i += 1
            tokens.append(("literal", source[start:i]))
            continue

        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            tokens.append(("identifier", source[start:i]))
            continue

        if ch.isdigit():
            start = i
            i += 1
            while i < n and (source[i].isalnum() or source[i] in "._"):
                i += 1
            tokens.append(("number", source[start:i]))
            continue

        found = False
        for op in MULTI_OPERATORS:
            if source.startswith(op, i):
                tokens.append(("operator", op))
                i += len(op)
                found = True
                break
        if found:
            continue

        if ch in "(){}[]":
            tokens.append(("delimiter", ch))
            i += 1
            continue

        tokens.append(("unknown", ch))
        i += 1

    return tokens

def count_statements(tokens):
    """
    Общее число операторов программы (statements языка Go,
    классическое представление — НЕ Холстед).

    Один statement на:
      - объявление func (с телом)
      - if / else if / else — ВСЯ цепочка = 1
      - for, switch, select
      - return, break, continue, goto, fallthrough
      - var, const, type — по 1 на декларацию
      - присваивание = / := / += и т.п.
      - ++ / --
      - вызов функции вида name(...)
    """
    count = 0
    n = len(tokens)
    i = 0

    while i < n:
        kind, value = tokens[i]

        if value == "func":
            count += 1
            i += 1
            continue

        if value == "package":
            count += 1
            i += 1
            continue

        if value == "import":
            count += 1
            # пропустить import-строку целиком
            if i + 1 < n and tokens[i + 1][1] == "(":
                d = 1
                i += 2
                while i < n and d > 0:
                    if tokens[i][1] == "(":
                        d += 1
                    elif tokens[i][1] == ")":
                        d -= 1
                    i += 1
            else:
                i += 1
                if i < n and tokens[i][0] == "identifier":
                    i += 1
                if i < n and tokens[i][0] == "literal":
                    i += 1
            continue

        if value == "if":
            prev = tokens[i - 1][1] if i > 0 else None
            if prev != "else":
                count += 1
            i += 1
            continue

        if value == "for":
            count += 1
            i += 1
            continue

        if value in ("switch", "select"):
            count += 1
            i += 1
            continue

        if value in ("return", "break", "continue", "goto", "fallthrough"):
            count += 1
            i += 1
            continue

        if value in ("var", "const", "type"):
            count += 1
            i += 1
            continue

        if kind == "operator" and value in (
            "=", ":=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=",
            "<<=", ">>=", "&^=", "++", "--",
        ):
            count += 1
            i += 1
            continue

        if kind == "identifier" and i + 1 < n and tokens[i + 1][1] == "(":
            if value not in GO_KEYWORDS:
                prev = tokens[i - 1][1] if i > 0 else None
                if prev not in (".", "func"):
                    count += 1
                i += 1
                continue

        i += 1

    return count

def compute_gilb(source):
    """
    Метрика Джилба:
      CL  — абсолютная сложность = сумма всех ветвлений
            (if / else if, for, switch/select: n ветвей дают n-1)
      cl  — CL / N, где N — statements языка (классическое представление)
      CLI — максимальная вложенность условий
            (switch с n ветвями эквивалентен n-1 if-else с вложенностью n-2)
    """
    tokens = lex_go(source)
    n = len(tokens)

    cl_holder = [0]
    max_depth_holder = [0]

    def matching_brace(start):
        d = 0
        for k in range(start, n):
            if tokens[k][1] == "{":
                d += 1
            elif tokens[k][1] == "}":
                d -= 1
                if d == 0:
                    return k
        return n

    def count_cases(start, end):
        """Считает case (без default) и наличие default на верхнем уровне."""
        nc = 0
        hd = False
        d = 0
        for k in range(start, end):
            v = tokens[k][1]
            if v == "{":
                d += 1
            elif v == "}":
                d -= 1
            elif d == 0:
                if v == "case":
                    nc += 1
                elif v == "default":
                    hd = True
        return nc, hd

    def process_block(start, end, base_depth):
        i = start
        while i < end:
            v = tokens[i][1]

            if v == "if":
                i = process_if_chain(i, end, base_depth)

            elif v == "for":
                cl_holder[0] += 1
                if base_depth > max_depth_holder[0]:
                    max_depth_holder[0] = base_depth
                j = i + 1
                while j < end and tokens[j][1] != "{":
                    j += 1
                if j >= end:
                    i += 1
                    continue
                close = matching_brace(j)
                process_block(j + 1, close, base_depth + 1)
                i = close + 1

            elif v in ("switch", "select"):
                j = i + 1
                while j < end and tokens[j][1] != "{":
                    j += 1
                if j >= end:
                    i += 1
                    continue
                close = matching_brace(j)
                nc, hd = count_cases(j + 1, close)
                nb = nc
                if nb >= 1:
                    cl_holder[0] += nb - 1
                    if nb >= 2:
                        eff = base_depth + nb - 2
                        if eff > max_depth_holder[0]:
                            max_depth_holder[0] = eff
                process_block(j + 1, close, base_depth + 1)
                i = close + 1

            elif v == "{":
                close = matching_brace(i)
                process_block(i + 1, close, base_depth)
                i = close + 1

            else:
                i += 1

    def process_if_chain(start, end, base_depth):
        i = start
        chain_pos = 0
        while i < end and tokens[i][1] == "if":
            cl_holder[0] += 1
            level = base_depth + chain_pos
            if level > max_depth_holder[0]:
                max_depth_holder[0] = level
            j = i + 1
            while j < end and tokens[j][1] != "{":
                j += 1
            if j >= end:
                return i + 1
            close = matching_brace(j)
            process_block(j + 1, close, level + 1)
            k = close + 1
            if k < end and tokens[k][1] == "else":
                if k + 1 < end and tokens[k + 1][1] == "if":
                    chain_pos += 1
                    i = k + 1
                    continue
                elif k + 1 < end and tokens[k + 1][1] == "{":
                    be = matching_brace(k + 1)
                    process_block(k + 2, be, level + 1)
                    return be + 1
                else:
                    return k + 1
            else:
                return close + 1
        return i

    process_block(0, n, 0)

    cl = cl_holder[0]
    cli = max_depth_holder[0]
    total = count_statements(tokens)
    cl_rel = (cl / total) if total else 0.0

    return {
        "cl": cl,
        "cl_rel": cl_rel,
        "cli": cli,
        "total": total,
    }

class GilbApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Метрика Джилба — Go")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)
        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Button(top, text="Открыть Go-файл", command=self.open_file).pack(side="left", padx=4)
        ttk.Button(top, text="Анализировать", command=self.analyze).pack(side="left", padx=4)
        ttk.Button(top, text="Очистить", command=self.clear).pack(side="left", padx=4)

        self.file_label = ttk.Label(top, text="Файл не выбран")
        self.file_label.pack(side="left", padx=12)

        main_pane = ttk.PanedWindow(self.root, orient="vertical")
        main_pane.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        source_frame = ttk.LabelFrame(main_pane, text="Исходный код Go", padding=6)
        main_pane.add(source_frame, weight=3)

        self.source = tk.Text(source_frame, wrap="none", font=("Consolas", 11))
        self.source.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(source_frame, orient="vertical", command=self.source.yview)
        scroll.pack(side="right", fill="y")
        self.source.configure(yscrollcommand=scroll.set)

        results_frame = ttk.Frame(main_pane, padding=2)
        main_pane.add(results_frame, weight=2)

        info = ttk.LabelFrame(results_frame, text="Метрика Джилба", padding=8)
        info.pack(fill="both", expand=True)

        self.cl_var = tk.StringVar(value="—")
        self.clrel_var = tk.StringVar(value="—")
        self.cli_var = tk.StringVar(value="—")
        self.total_var = tk.StringVar(value="—")

        rows = [
            ("CL", "Абсолютная сложность — сумма всех ветвлений (if / else if / for / switch)", self.cl_var),
            ("cl", "Относительная сложность: cl = CL / N", self.clrel_var),
            ("CLI", "Максимальный уровень вложенности условий", self.cli_var),
            ("N", "Общее число операторов программы (statements языка)", self.total_var),
        ]

        for row_idx, (label, desc, var) in enumerate(rows):
            ttk.Label(info, text=label, font=("Consolas", 13, "bold")).grid(
                row=row_idx, column=0, sticky="w", padx=(4, 12), pady=6
            )
            ttk.Label(info, textvariable=var, font=("Consolas", 13)).grid(
                row=row_idx, column=1, sticky="w", padx=(0, 16), pady=6
            )
            ttk.Label(info, text=desc, foreground="#555").grid(
                row=row_idx, column=2, sticky="w", padx=(0, 4), pady=6
            )

        info.columnconfigure(2, weight=1)

        hint = ttk.Label(
            results_frame,
            text="N считается по statements языка: if-цепочка = 1, каждый return = 1, "
                 "каждое присваивание = 1. Switch с n ветвями даёт n-1 к CL и n-2 к CLI.",
            anchor="w",
            foreground="#666",
        )
        hint.pack(fill="x", pady=(6, 0))

    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите Go-файл",
            filetypes=[("Go files", "*.go"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filename, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except OSError as err:
            messagebox.showerror("Ошибка", str(err))
            return

        self.source.delete("1.0", "end")
        self.source.insert("1.0", content)
        self.file_label.configure(text=filename)

    def analyze(self):
        src = self.source.get("1.0", "end-1c")
        if not src.strip():
            messagebox.showwarning("Нет исходного кода", "Введите или загрузите программу на Go.")
            return
        try:
            m = compute_gilb(src)
        except Exception as err:
            messagebox.showerror("Ошибка анализа", f"Не удалось выполнить анализ:\n{err}")
            return

        self.cl_var.set(str(m["cl"]))
        self.clrel_var.set(f'{m["cl_rel"]:.3f}')
        self.cli_var.set(str(m["cli"]))
        self.total_var.set(str(m["total"]))

    def clear(self):
        self.source.delete("1.0", "end")
        self.file_label.configure(text="Файл не выбран")
        for var in (self.cl_var, self.clrel_var, self.cli_var, self.total_var):
            var.set("—")

if __name__ == "__main__":
    root = tk.Tk()
    app = GilbApp(root)
    root.mainloop()
