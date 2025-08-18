from flask import Flask, request, jsonify, render_template
import re

app = Flask(__name__)

# ------- Simple educational "compiler" -------

TOKEN_SPEC = [
    ('INT',     r'\bint\b'),
    ('PRINT',   r'\bprint\b'),
    ('ID',      r'[A-Za-z_]\w*'),
    ('NUM',     r'\b\d+\b'),
    ('ASSIGN',  r'='),
    ('PLUS',    r'\+'),
    ('MINUS',   r'-'),
    ('MUL',     r'\*'),
    ('DIV',     r'/'),
    ('LPAREN',  r'\('),
    ('RPAREN',  r'\)'),
    ('COMMA',   r','),
    ('SEMI',    r';'),
    ('NEWLINE', r'\n'),
    ('SKIP',    r'[ \t\r]+'),
    ('MISMATCH',r'.'),
]
TOKEN_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for name,pattern in TOKEN_SPEC))

def lex(source: str):
    tokens = []
    line = 1
    col = 1
    for m in TOKEN_REGEX.finditer(source):
        kind = m.lastgroup
        text = m.group()
        if kind == 'NEWLINE':
            line += 1
            col = 1
            continue
        if kind == 'SKIP':
            col += len(text)
            continue
        if kind == 'MISMATCH':
            tokens.append({'type': 'ERROR', 'lexeme': text, 'line': line, 'col': col})
            col += len(text)
            continue
        tokens.append({'type': kind, 'lexeme': text, 'line': line, 'col': col})
        col += len(text)
    return tokens

# Very tiny grammar (program = decls stmts)
# Declarations:  int a, b;
# Assign:        a = 3 + 4 * 2;
# Print:         print(a);
#
# We'll parse only ID/NUM and +,-,*,/, parentheses, assignment, print.

class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0
        self.symbols = []   # [{'name':..., 'type':'int', 'scope':'global'}]
        self.temp_counter = 1
        self.tac = []       # list of strings
        self.errors = []

    def peek(self, kind=None):
        if self.i >= len(self.toks): return None
        t = self.toks[self.i]
        if kind and t['type'] != kind: return None
        return t

    def eat(self, kind):
        t = self.peek(kind)
        if not t:
            self.errors.append(f"Expected {kind} at token {self.i+1}")
            return None
        self.i += 1
        return t

    def at_end(self):
        return self.i >= len(self.toks)

    # program: decl_list stmt_list
    def parse_program(self):
        decls = self.parse_decl_list()
        stmts = self.parse_stmt_list()
        return {'node':'Program','children':[decls, stmts]}

    def parse_decl_list(self):
        items = []
        while self.peek('INT'):
            items.append(self.parse_decl())
        return {'node':'DeclList','children':items}

    def parse_decl(self):
        self.eat('INT')
        ids = self.parse_id_list()
        self.eat('SEMI')
        # record in symbol table
        for name in ids:
            if not any(s['name']==name for s in self.symbols):
                self.symbols.append({'name': name, 'type': 'int', 'scope': 'global'})
        return {'node':'Decl','ids':ids}

    def parse_id_list(self):
        names = []
        t = self.eat('ID')
        if t: names.append(t['lexeme'])
        while self.peek('COMMA'):
            self.eat('COMMA')
            t2 = self.eat('ID')
            if t2: names.append(t2['lexeme'])
        return names

    def parse_stmt_list(self):
        items = []
        # stmt starts with ID or PRINT
        while True:
            if self.peek('ID'):
                items.append(self.parse_assign())
            elif self.peek('PRINT'):
                items.append(self.parse_print())
            else:
                break
        return {'node':'StmtList','children':items}

    def parse_assign(self):
        idtok = self.eat('ID')
        self.eat('ASSIGN')
        expr_node, place = self.parse_expr()
        self.eat('SEMI')
        # TAC: id = place
        if idtok and place is not None:
            self.tac.append(f"{idtok['lexeme']} = {place}")
        return {'node':'Assign','id': idtok['lexeme'] if idtok else '?', 'expr': expr_node}

    def parse_print(self):
        self.eat('PRINT'); self.eat('LPAREN')
        idtok = self.eat('ID')
        self.eat('RPAREN'); self.eat('SEMI')
        # TAC: print id
        if idtok:
            self.tac.append(f"print {idtok['lexeme']}")
        return {'node':'Print','id': idtok['lexeme'] if idtok else '?'}

    # expr with precedence: term ((+|-) term)*
    def parse_expr(self):
        node, place = self.parse_term()
        while self.peek('PLUS') or self.peek('MINUS'):
            op = 'PLUS' if self.peek('PLUS') else 'MINUS'
            self.eat(op)
            node2, place2 = self.parse_term()
            t = self.new_temp()
            self.tac.append(f"{t} = {place} {'+' if op=='PLUS' else '-'} {place2}")
            node = {'node':'BinOp','op':'+' if op=='PLUS' else '-','left':node,'right':node2}
            place = t
        return node, place

    # term: factor ((*|/) factor)*
    def parse_term(self):
        node, place = self.parse_factor()
        while self.peek('MUL') or self.peek('DIV'):
            op = 'MUL' if self.peek('MUL') else 'DIV'
            self.eat(op)
            node2, place2 = self.parse_factor()
            t = self.new_temp()
            self.tac.append(f"{t} = {place} {'*' if op=='MUL' else '/'} {place2}")
            node = {'node':'BinOp','op':'*' if op=='MUL' else '/','left':node,'right':node2}
            place = t
        return node, place

    def parse_factor(self):
        if self.peek('LPAREN'):
            self.eat('LPAREN')
            node, place = self.parse_expr()
            self.eat('RPAREN')
            return node, place
        if self.peek('NUM'):
            t = self.eat('NUM')
            return {'node':'Num','value':int(t['lexeme'])}, t['lexeme']
        if self.peek('ID'):
            t = self.eat('ID')
            return {'node':'Var','name':t['lexeme']}, t['lexeme']
        self.errors.append("Expected (expr) | NUM | ID")
        return {'node':'Error'}, None

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

def generate_nasm_like(symbols, tac):
    # tiny, illustrative NASM-like text (not executed here)
    lines = []
    lines.append("section .data")
    for s in symbols:
        lines.append(f"{s['name']} dq 0")
    lines.append("section .text")
    lines.append("global _start")
    lines.append("_start:")
    # Convert TAC to very rough asm (illustrative only)
    for instr in tac:
        if instr.startswith("print "):
            var = instr.split()[1]
            lines.append(f"    ; print {var} (stub)")
        elif '=' in instr:
            left, right = [x.strip() for x in instr.split('=', 1)]
            parts = right.split()
            if len(parts) == 1:
                lines.append(f"    ; {left} = {right}")
            elif len(parts) == 3:
                a, op, b = parts
                opm = {'+':'add', '-':'sub', '*':'imul', '/':'idiv'}.get(op, 'add')
                lines.append(f"    ; {left} = {a} {op} {b}")
                lines.append(f"    ; {opm} (omitted real moves for brevity)")
    lines.append("    ; exit(0) stub")
    return "\n".join(lines)

def compile_source(source: str):
    tokens = lex(source)
    # Basic error check: if any ERROR tokens exist
    if any(t['type']=='ERROR' for t in tokens):
        errs = [f"Lexical error: Unexpected character '{t['lexeme']}' at line {t['line']}, column {t['col']}"
                for t in tokens if t['type']=='ERROR']
        return {'success': False, 'errors': errs, 'tokens': tokens}

    p = Parser(tokens)
    parse_tree = p.parse_program()

    asm = generate_nasm_like(p.symbols, p.tac)

    return {
        'success': len(p.errors) == 0,
        'errors': p.errors,
        'tokens': tokens,
        'symbolTable': p.symbols,
        'parseTree': parse_tree,
        'tac': p.tac,
        'assembly': asm
    }

# --------------- Flask routes ---------------

@app.route('/')
def index():
    return render_template('index.html', title='Educational Compiler')

@app.post('/compile')
def api_compile():
    data = request.get_json(silent=True) or {}
    src = data.get('source', '')
    result = compile_source(src)
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)  