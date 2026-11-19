---
name: analizador-sintactico-mini-c
description: Especificación del analizador sintáctico de Mini-C definida por Lorem Ipsum. Úsala para implementar, probar o corregir src/minic/parser/parser.py del proyecto modular minic: recibe la lista de tokens del lexer y devuelve el AST y los diagnósticos SYN001-SYN003.
---

# Analizador sintáctico de Mini-C

Especificación elaborada por **Lorem Ipsum** (grupo 1SF-132) en el Proyecto N°2 de Lenguajes Formales y Autómatas (UTP-FISC). Implementa el parser **exactamente** como se describe aquí. Si algo no está definido o se contradice, pregunta antes de asumir; no inventes reglas, nodos ni códigos de diagnóstico.

## 0. Alcance y restricciones (obligatorio)

1. Trabaja sobre el proyecto modular `minic` existente (el mismo software del Proyecto 1). Ejecuta desde la raíz del proyecto con `PYTHONPATH=src`.
2. **El único archivo que puedes modificar es `src/minic/parser/parser.py`.** No crees, borres ni modifiques ningún otro archivo: ni `lexer/`, ni `diagnostics/`, ni `syntax_tree/`, ni `parser/parser_result.py`, ni `compiler.py`, ni `__init__.py`, ni las pruebas.
3. No definas clases propias de tokens, nodos, diagnósticos ni resultados. Importa exactamente:
```python
from minic.diagnostics import diagnostic_code
from minic.diagnostics.diagnostic_bag import DiagnosticBag
from minic.lexer.token import Token
from minic.lexer.token_type import TokenType
from minic.parser.parser_result import ParserResult
from minic.syntax_tree.expressions import BinaryExpression, ComparisonExpression, Expression, IdentifierExpression, IntegerLiteral
from minic.syntax_tree.program import Program
from minic.syntax_tree.statements import Assignment, Statement, VariableDeclaration, WhileStatement
```
4. **Contrato.** Entrada: la lista que entrega `Lexer(source).scan()`, terminada en un único `EOF` y sin errores LEX (el coordinador no llama al parser si los hay). Salida: `Parser(tokens).parse()` devuelve `ParserResult(program, diagnostics)`: `program` es el AST (`Program`, **nunca** `None`, aunque haya diagnósticos) y `diagnostics` es la lista de diagnósticos SYN en orden de aparición.
5. Compara categorías por igualdad de cadena con las constantes de `TokenType` (`TokenType.KW_INT == "KW_INT"`).

## 1. Gramática de Mini-C (EBNF del grupo)

```text
Program = { Statement } EOF ;
Statement = Declaration | Assignment | while_stmt ;
Declaration = KW_INT IDENTIFIER [ ASSIGN expression ] SEMICOLON ;
Assignment = IDENTIFIER ASSIGN expression SEMICOLON ;
while_stmt = KW_WHILE LPAREN condition RPAREN block ;
block = LBRACE { Statement } RBRACE ;
condition = expression ( EQUAL_EQUAL | NOT_EQUAL ) expression ;
expression = Primary { ( PLUS | MINUS ) Primary } ;
Primary = INTEGER_LITERAL | IDENTIFIER | LPAREN expression RPAREN ;
```

## 2. Gramática preparada para decisiones predictivas

```text
program -> statement_list EOF
statement_list -> statement statement_list | ε
statement -> declaration | assignment | while_stmt
declaration -> KW_INT IDENTIFIER initializer SEMICOLON
initializer -> ASSIGN expression | ε
assignment -> IDENTIFIER ASSIGN expression SEMICOLON
while_stmt -> KW_WHILE LPAREN condition RPAREN block
block -> LBRACE statement_list RBRACE
condition -> expression comparison_op expression
comparison_op -> EQUAL_EQUAL | NOT_EQUAL
expression -> primary tail
tail -> PLUS primary tail | MINUS primary tail | ε
primary -> INTEGER_LITERAL | IDENTIFIER | LPAREN expression RPAREN
```

Transformaciones acordadas por el grupo:

- `expression -> expression PLUS primary | expression MINUS primary | primary` ⇒
```text
expression -> primary tail
tail -> PLUS primary tail | MINUS primary tail | ε
```
- `statement_list -> statement_list statement | ε` ⇒
```text
statement_list -> statement statement_list | ε
```
- `declaration -> KW_INT IDENTIFIER SEMICOLON | KW_INT IDENTIFIER ASSIGN expression SEMICOLON` ⇒
```text
declaration -> KW_INT IDENTIFIER decl_rest
decl_rest -> SEMICOLON | ASSIGN expression SEMICOLON
```

## 3. Anulables, FIRST, FOLLOW y SELECT (según el grupo)

Anulables: `statement_list`, `initializer`, `tail`

| No terminal | FIRST | FOLLOW |
|---|---|---|
| `program` | `{KW_INT, KW_WHILE, IDENTIFIER, EOF}` | `{⊣}` |
| `statement_list` | `{KW_INT, KW_WHILE, IDENTIFIER, ε}` | `{EOF, RBRACE}` |
| `statement` | `{KW_INT, KW_WHILE, IDENTIFIER}` | `{KW_INT, KW_WHILE, IDENTIFIER, EOF, RBRACE}` |
| `declaration` | `{KW_INT}` | `{KW_INT, KW_WHILE, IDENTIFIER, RBRACE, EOF}` |
| `initializer` | `{ASSIGN, ε}` | `{SEMICOLON}` |
| `assignment` | `{IDENTIFIER}` | `{KW_INT, KW_WHILE, IDENTIFIER, RBRACE, EOF}` |
| `while_stmt` | `{KW_WHILE}` | `{KW_INT, KW_WHILE, IDENTIFIER, RBRACE, EOF}` |
| `block` | `{LBRACE}` | `{KW_INT, KW_WHILE, IDENTIFIER, RBRACE, EOF}` |
| `condition` | `{IDENTIFIER, INTEGER_LITERAL, LPAREN}` | `{RPAREN}` |
| `comparison_op` | `{EQUAL_EQUAL, NOT_EQUAL}` | `{INTEGER_LITERAL, IDENTIFIER, LPAREN}` |
| `expression` | `{INTEGER_LITERAL, IDENTIFIER, LPAREN}` | `{SEMICOLON, EQUAL_EQUAL, NOT_EQUAL, RPAREN}` |
| `tail` | `{PLUS, MINUS, ε}` | `{SEMICOLON, EQUAL_EQUAL, NOT_EQUAL, RPAREN}` |
| `primary` | `{INTEGER_LITERAL, IDENTIFIER, LPAREN}` | `{EQUAL_EQUAL, NOT_EQUAL, RPAREN, SEMICOLON, PLUS, MINUS}` |

| Producción | SELECT |
|---|---|
| `program → statement_list EOF` | `{KW_INT, KW_WHILE, IDENTIFIER, EOF}` |
| `statement_list → statement statement_list` | `{KW_INT, KW_WHILE, IDENTIFIER}` |
| `statement_list → ε` | `{EOF, RBRACE}` |
| `statement → declaration` | `{KW_INT}` |
| `statement → assignment` | `{IDENTIFIER}` |
| `statement → while_stmt` | `{KW_WHILE}` |
| `declaration → KW_INT IDENTIFIER initializer SEMICOLON` | `{KW_INT}` |
| `initializer → ASSIGN expression` | `{ASSIGN}` |
| `initializer → ε` | `{SEMICOLON}` |
| `assignment → IDENTIFIER ASSIGN expression SEMICOLON` | `{IDENTIFIER}` |
| `while_stmt → KW_WHILE LPAREN condition RPAREN block` | `{KW_WHILE}` |
| `block → LBRACE statement_list RBRACE` | `{LBRACE}` |
| `condition → expression comparison_op expression` | `{INTEGER_LITERAL, IDENTIFIER, LPAREN}` |
| `comparison_op → EQUAL_EQUAL` | `{EQUAL_EQUAL}` |
| `comparison_op → NOT_EQUAL` | `{NOT_EQUAL}` |
| `expression → primary tail` | `{IDENTIFIER, INTEGER_LITERAL, LPAREN}` |
| `tail → PLUS primary tail` | `{PLUS}` |
| `tail → MINUS primary tail` | `{MINUS}` |
| `tail → ε` | `{SEMICOLON, EQUAL_EQUAL, NOT_EQUAL, RPAREN}` |
| `primary → INTEGER_LITERAL` | `{INTEGER_LITERAL}` |
| `primary → IDENTIFIER` | `{IDENTIFIER}` |
| `primary → LPAREN expression RPAREN` | `{LPAREN}` |

## 4. Tabla predictiva LL(1) (celdas llenas, según el grupo)

- M[program, KW_INT] = program → statement_list EOF
- M[program, KW_WHILE] = program → statement_list EOF
- M[program, IDENTIFIER] = program → statement_list EOF
- M[program, EOF] = program → statement_list EOF
- M[statement_list, KW_INT] = statement_list → statement statement_list
- M[statement_list, KW_WHILE] = statement_list → statement statement_list
- M[statement_list, IDENTIFIER] = statement_list → statement statement_list
- M[statement_list, RBRACE] = statement_list → ε
- M[statement_list, EOF] = statement_list → ε
- M[statement, KW_INT] = statement → declaration
- M[statement, KW_WHILE] = statement → while_stmt
- M[statement, IDENTIFIER] = statement → assignment
- M[declaration, KW_INT] = declaration → KW_INT IDENTIFIER initializer SEMICOLON
- M[initializer, ASSIGN] = initializer → ASSIGN expression
- M[initializer, SEMICOLON] = initializer → ε
- M[assignment, IDENTIFIER] = assignment → IDENTIFIER ASSIGN expression SEMICOLON
- M[while_stmt, KW_WHILE] = while_stmt → KW_WHILE LPAREN condition RPAREN block
- M[block, LBRACE] = block → LBRACE statement_list RBRACE
- M[condition, IDENTIFIER] = condition → expression comparison_op expression
- M[condition, INTEGER_LITERAL] = condition → expression comparison_op expression
- M[condition, LPAREN] = condition → expression comparison_op expression
- M[comparison_op, EQUAL_EQUAL] = comparison_op → EQUAL_EQUAL
- M[comparison_op, NOT_EQUAL] = comparison_op → NOT_EQUAL
- M[expression, IDENTIFIER] = expression → primary tail
- M[expression, INTEGER_LITERAL] = expression → primary tail
- M[expression, LPAREN] = expression → primary tail
- M[tail, PLUS] = tail → PLUS primary tail
- M[tail, MINUS] = tail → MINUS primary tail
- M[tail, EQUAL_EQUAL] = tail → ε
- M[tail, NOT_EQUAL] = tail → ε
- M[tail, RPAREN] = tail → ε
- M[tail, SEMICOLON] = tail → ε
- M[primary, IDENTIFIER] = primary → IDENTIFIER
- M[primary, INTEGER_LITERAL] = primary → INTEGER_LITERAL
- M[primary, LPAREN] = primary → LPAREN expression RPAREN

Toda celda no listada es de error. Cada decisión del parser descendente (qué método llamar, cuándo repetir un bucle, cuándo omitir una parte opcional) debe corresponder a esta tabla.

## 5. Un método por no terminal

| Método | Construcción | Devuelve |
|---|---|---|
| `parse` | entrada pública | `ParserResult(program, diagnostics)` |
| `parse_program` | cero o más instrucciones hasta `EOF` | `Program` |
| `parse_statement` | decide por `KW_INT`, `KW_WHILE` o `IDENTIFIER` | `Statement` o `None` si descarta un token |
| `parse_declaration` | `int` nombre e inicializador opcional | `VariableDeclaration` |
| `parse_assignment` | nombre `=` expresión | `Assignment` |
| `parse_while` | `while ( condición ) bloque` | `WhileStatement` |
| `parse_block` | `{` instrucciones hasta `}` o `EOF` | tupla de instrucciones |
| `parse_condition` | expresión, `==`/`!=`, expresión | `ComparisonExpression` |
| `parse_expression` | términos con `+`/`-` en un bucle, asociando a la izquierda | `Expression` |
| `parse_term` | literal, nombre o `( expresión )` | `Expression` |

Utilidades del cursor: `peek()` (no consume), `check(tipo)` (no consume), `advance()` (consume salvo en `EOF`) y `expect(tipo, código, mensaje)` (consume si coincide; si no, registra el diagnóstico en la posición del token actual, devuelve `None` y **no consume**).

Precedencia y asociatividad según el grupo:

- Nivel 1 · cima: se agrupa primero: `nombre (IDENTIFIER)`, `literal entero`, `( expresión )` — asociatividad: no aplica (es una unidad)
- Nivel 2: `+`, `- (resta)` — asociatividad: izquierda
- Nivel 3 · base: se agrupa al final: `==`, `!=` — asociatividad: no asociativa (aparece una sola vez)
- No existen en Mini-C (no implementarlos): `*`, `/`, `- unario (−x)`, `<`, `= dentro de una expresión`

## 6. Contrato del AST

| Nodo | Campos | `line`/`column` tomados de |
|---|---|---|
| `Program` | statements (tupla) | primer token, incluido `EOF` si la fuente está vacía |
| `VariableDeclaration` | name, initializer (o `None`) | la palabra `int` |
| `Assignment` | name, value | el nombre de destino |
| `WhileStatement` | condition, body (tupla) | la palabra `while` |
| `ComparisonExpression` | left, operator, right | el hijo izquierdo |
| `BinaryExpression` | left, operator, right | el hijo izquierdo |
| `IdentifierExpression` | name | su token |
| `IntegerLiteral` | value (int del lexer) | su token |

Qué construye cada regla, según el grupo:

- `program = { statement } EOF` → Program
- `statement = declaration | assignment | while_stmt` → No crea nodo propio
- `declaration = KW_INT IDENTIFIER [ ASSIGN expression ] SEMICOLON` → VariableDeclaration
- `assignment = IDENTIFIER ASSIGN expression SEMICOLON` → Assignment
- `while_stmt = KW_WHILE LPAREN condition RPAREN block` → WhileStatement
- `block = LBRACE { statement } RBRACE` → No crea nodo propio
- `condition = expression ( EQUAL_EQUAL | NOT_EQUAL ) expression` → ComparisonExpression
- `cada PLUS o MINUS dentro de expression` → BinaryExpression
- `primary → INTEGER_LITERAL` → IntegerLiteral
- `primary → IDENTIFIER` → IdentifierExpression
- `primary → LPAREN expression RPAREN` → No crea nodo propio

`int x;` tiene `initializer=None` (nunca un 0 inventado). Árboles definidos por el grupo:

```text
x = x - (1 + 2);
Program
  statements[0]: Assignment x
    value: BinaryExpression -
      left: IdentifierExpression x
      right: BinaryExpression +
        left: IntegerLiteral 1
        right: IntegerLiteral 2

int y = a - b - c;
Program
  statements[0]: VariableDeclaration y
    initializer: BinaryExpression -
      left: BinaryExpression -
        left: IdentifierExpression a
        right: IdentifierExpression b
      right: IdentifierExpression c

int s = 0; while (s != 5) { s = s + 1; }
Program
  statements[0]: VariableDeclaration s
    initializer: IntegerLiteral 0
  statements[1]: WhileStatement
    condition: ComparisonExpression !=
      left: IdentifierExpression s
      right: IntegerLiteral 5
    body[0]: Assignment s
      value: BinaryExpression +
        left: IdentifierExpression s
        right: IntegerLiteral 1
```

## 7. Diagnósticos y recuperación

- `SYN001` «Se esperaba ';'»: declaración y asignación.
- `SYN002` «Se esperaba ')'»: agrupación aritmética y condición del `while`.
- `SYN003` «Se esperaba '}'»: cierre de bloque.
- Severidad `error`; posición del token actual al fallar `expect`. No se crean otros códigos ni excepciones (`ParseError` no existe).
- Registra con `self._diagnostics.report(código, mensaje, línea, columna)` usando las constantes y funciones de `diagnostic_code` (`diagnostic_code.SYN001` con `diagnostic_code.expected_semicolon()`, `SYN002` con `expected_right_paren()`, `SYN003` con `expected_right_brace()`). `parse()` devuelve `ParserResult(program, self._diagnostics.to_list())`.
- Recuperación: `parse_statement` descarta un token que no inicia instrucción y devuelve `None`; `parse_term` descarta un token que no inicia término y devuelve `IntegerLiteral(0)` en esa posición; el nombre tras `int`, el `=` de la asignación, las aperturas `(` y `{` y el comparador se consumen suponiendo que están presentes. El parser nunca debe quedarse detenido.

## 8. Casos de prueba que el agente debe verificar

Diagnósticos y descartes esperados según el grupo:

```c
int a = 5;
while (a == 0) {
    a = a + 1
}
```
→ diagnósticos: SYN001 4:1; tokens descartados: ninguno

```c
x = (1 + 2;
```
→ diagnósticos: SYN002 1:11; tokens descartados: ninguno

```c
while (y != 1) {
    int z = (y - 1;
}
```
→ diagnósticos: SYN002 2:19; tokens descartados: ninguno

```c
int b = 2;
b = b - 1;
```
→ diagnósticos: ninguno; tokens descartados: ninguno

```c
while (n != 0) {
    n = n - 1;
```
→ diagnósticos: SYN003 2:15; tokens descartados: ninguno

```c
x = 1;
) x = 2;
```
→ diagnósticos: ninguno; tokens descartados: `)`

Gramática frente a implementación, según el grupo:

| Fuente | ¿La gramática la acepta? | Diagnósticos del parser |
|---|---|---|
| `;` | No | ninguno |
| `int x; }` | No | ninguno |
| `int x = ;` | No | SYN001 1:10 |
| `int ;` | No | SYN001 1:6 |
| `while (x) {}` | No | SYN002 1:12, SYN003 1:13 |
| `int x = 1 2;` | No | SYN001 1:11 |

## 9. Instrucciones para el agente

1. Lee primero `src/minic/parser/parser.py`, `parser_result.py`, los nodos de `syntax_tree/` y `diagnostics/` para confirmar nombres y firmas; **solo lectura** fuera de `parser.py`.
2. Implementa (o corrige) `Parser` en `src/minic/parser/parser.py` siguiendo las secciones 1–7: recibe los tokens del lexer y devuelve el AST y los diagnósticos.
3. Ejecuta los casos de la sección 8 con `compile_source(fuente, stages=("lexer", "parser"))` y compara. Si difieren, informa qué regla de esta especificación produce la diferencia en lugar de cambiar la regla por tu cuenta.
4. Corre `python -m pytest`. **No modifiques ninguna prueba.** Al implementar el parser es esperado que fallen solo las pruebas del esqueleto que exigen que la etapa siga sin implementar (`test_parser_is_stub` y, si el lexer ya existe, `test_lexer_is_stub` y la prueba de la CLI que espera el código 3); repórtalas como esperadas. Cualquier otra falla es un error tuyo. `tests/parser/` puede no tener pruebas todavía: en ese caso tu verificación son los casos de la sección 8.
5. Si la especificación del grupo contradice el contrato del proyecto (por ejemplo, una gramática que no es LL(1) o un diagnóstico imposible), señálalo antes de continuar.