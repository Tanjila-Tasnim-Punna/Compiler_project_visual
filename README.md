# Educational Visual Compiler

A web-based teaching tool that shows beginners **what a compiler does at each phase**. You type a small program in the browser, and the tool shows the tokens, symbol table, parse tree, three-address code and assembly it produces, along with clear error messages.

Built as a Compiler Design course project at Daffodil International University.

## Features

- **Lexical analysis**: a token table showing each token's type, lexeme and line
- **Symbol table**: declared variables with their type and scope
- **Parse tree**: an interactive tree drawn with D3.js
- **Intermediate code**: three-address code (TAC) with temporaries
- **Code generation**: illustrative NASM-style assembly
- **Error reporting**: lexical and syntax errors with line and column

## Example

Input:

```c
int a, b;
a = 3 + 4 * 2;
b = (a - 1) / 2;
print(b);
```

Generated three-address code (operator precedence is respected):

```
t1 = 4 * 2
t2 = 3 + t1
a = t2
t3 = a - 1
t4 = t3 / 2
b = t4
print b
```

## Supported language

| Construct | Example |
|---|---|
| Declarations | `int a, b;` |
| Assignment | `a = 3 + 4 * 2;` |
| Arithmetic | `+ - * /` and parentheses |
| Output | `print(a);` |

## Tech stack

`Python` `Flask` `JavaScript` `D3.js` `HTML/CSS`

## How it works

```
source code → Lexer (regex) → Recursive-descent parser → Symbol table
                                     ↓
                     Parse tree + three-address code → NASM-style assembly
```

- `app.py`: the lexer, a recursive-descent parser, TAC generation and the Flask API (`POST /compile`)
- `static/app.js`: sends the code to the API and renders each phase (the D3 tree, tables)
- `templates/index.html`: the UI with a tab for each phase

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000.

## Author

**Tanjila Tasnim Punna**, CSE, Daffodil International University
[LinkedIn](https://linkedin.com/in/tanjila-tasnim-a419b2267)
