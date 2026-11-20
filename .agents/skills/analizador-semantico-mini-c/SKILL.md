---
name: analizador-semantico-mini-c
description: Especificación del analizador semántico de Mini-C definida por Lorem Ipsum. Úsala para implementar, probar o corregir src/minic/semantic/symbol_table.py y src/minic/semantic/semantic_analyzer.py del proyecto modular minic: recibe el Program del parser y devuelve SemanticResult(symbols, diagnostics) con SEM001-SEM004.
---

# Analizador semántico de Mini-C

Especificación elaborada por **Lorem Ipsum** (grupo ISF-132) en el Proyecto N°3 de Lenguajes Formales y Autómatas (UTP-FISC). Implementa la etapa **exactamente** como se describe aquí. Si algo no está definido o se contradice, pregunta antes de asumir; no inventes reglas, campos, ámbitos ni códigos.

## 0. Alcance y restricciones (obligatorio)

1. Trabaja sobre el proyecto modular `minic` existente (el mismo de los Proyectos 1 y 2), desde la raíz con `PYTHONPATH=src`.
2. **Solo puedes modificar dos archivos: `src/minic/semantic/symbol_table.py` y `src/minic/semantic/semantic_analyzer.py`.** No crees, borres ni modifiques nada más: ni `symbol.py`, ni `semantic_result.py`, ni `__init__.py`, ni `syntax_tree/`, ni `diagnostics/`, ni `lexer/`, ni `parser/`, ni `compiler.py`, ni las pruebas.
3. Conserva las firmas, docstrings e importaciones de los esqueletos. No definas clases propias de símbolos, nodos, diagnósticos ni resultados; usa `Symbol`, `SemanticResult`, `DiagnosticBag`, `diagnostic_code` y los nodos de `minic.syntax_tree`.
4. **Contrato.** Entrada: la raíz `Program` que entrega `Parser(tokens).parse()` (no los tokens ni el `ParserResult`). Salida: `SemanticAnalyzer(program).analyze()` devuelve `SemanticResult(self._table.symbols(), self._diagnostics.to_list())`. El AST no se modifica ni se anota.
5. Mini C tiene **una sola tabla global**: el cuerpo de `while` no abre ámbito, no se eliminan símbolos al terminar el cuerpo y el único tipo es `"INT"`. No implementes ámbitos anidados, tipos `bool` ni inicialización garantizada por caminos.

## 1. SymbolTable (`symbol_table.py`)

- Diccionario `self._symbols: dict[str, Symbol]` y un contador del siguiente id, que empieza en 1. Los nombres distinguen mayúsculas.
- `declare(name, declared_line, initialized)`: si `name` ya existe devuelve `None` sin cambiar nada (no consume id); si no, crea `Symbol(id, name, "INT", initialized, declared_line)`, lo guarda y lo devuelve.
- `lookup(name)`: devuelve el `Symbol` o `None`; nunca inserta.
- `mark_initialized(name)`: precondición: `name` existe (si no, `KeyError` de Python, no un diagnóstico). Usa `dataclasses.replace(symbol, initialized=True)`, guarda la copia bajo la misma clave y la devuelve; conserva id, nombre, tipo y línea.
- `symbols()`: lista **nueva** en orden de id.

Traza acordada por el grupo sobre una tabla nueva:

| Operación | Devuelve | ¿Cambia la tabla? |
|---|---|---|
| `declare("x", 1, False)` | Symbol(1, 'x', 'INT', False, 1) | Sí |
| `lookup("y")` | None | No |
| `declare("x", 3, True)` | None | No |
| `declare("y", 4, True)` | Symbol(2, 'y', 'INT', True, 4) | Sí |
| `mark_initialized("x")` | Symbol(1, 'x', 'INT', True, 1) | Sí |
| `lookup("x")` | Symbol(1, 'x', 'INT', True, 1) | No |
| `mark_initialized("z")` | KeyError: precondición incumplida | No |
| `symbols()` | [x, y] en orden de id | No |

## 2. Reglas y diagnósticos (`semantic_analyzer.py`)

| Código | Cuándo | Mensaje (usar `diagnostic_code`) | Posición |
|---|---|---|---|
| `SEM001` | se lee o se asigna un nombre que `lookup` no encuentra | `undeclared_variable(name)` | nodo `IdentifierExpression` leído, o nodo `Assignment` (nombre destino) |
| `SEM002` | `declare` devuelve `None` | `redeclared_variable(name)` | nodo `VariableDeclaration` (la palabra `int`) |
| `SEM003` | se lee un nombre existente con `initialized=False` | `uninitialized_variable(name)` | nodo `IdentifierExpression` leído |
| `SEM004` | la condición de `while` no es `ComparisonExpression` | `invalid_operation("la condición de 'while' debe ser una comparación")` | nodo de la condición |

Se registran con `self._diagnostics.report(código, mensaje, nodo.line, nodo.column)` usando las constantes `diagnostic_code.SEM00X`. Para una sola lectura se reporta `SEM001` **o** `SEM003`, nunca ambos.

## 3. Recorrido (orden obligatorio)

- `analyze`: recorre `program.statements` en orden con `_visit_statement` y construye el resultado.
- `_visit_statement`: despacha con `isinstance` a declaración, asignación o ciclo.
- `_visit_declaration`: **primero** visita el inicializador (si existe) con `_visit_expression`; **después** `declare(name, node.line, initializer is not None)`; si devuelve `None`, `SEM002`. Por eso `int x = x;` da `SEM001` en el `x` derecho, y una declaración con inicializador queda `initialized=True` aunque el inicializador tenga errores. La redeclaración no marca el símbolo original.
- `_visit_assignment`: **primero** visita `value`; **después** busca `name`: si no existe, `SEM001` en el nodo `Assignment` (no se registra símbolo); si existe, `mark_initialized`. El destino es texto, no se visita como lectura.
- `_visit_while`: `_check_condition(condition)` y luego cada instrucción de `body` **una sola vez**; las actualizaciones persisten.
- `_check_condition`: si es `ComparisonExpression`, visita `left` y luego `right`; si no, reporta `SEM004` y después visita esa expresión con `_visit_expression`.
- `_visit_expression`: `IdentifierExpression` → SEM001/SEM003; `BinaryExpression` → `left` y luego `right`; `IntegerLiteral` → nada.

Responsabilidades según el grupo:

- recorrer Program.statements y devolver SemanticResult → `analyze`
- elegir la visita según la clase de la instrucción → `_visit_statement`
- VariableDeclaration: revisar el inicializador y después declarar → `_visit_declaration`
- Assignment: revisar el valor y después buscar y marcar el destino → `_visit_assignment`
- WhileStatement: condición y luego cada instrucción del cuerpo → `_visit_while`
- condición ComparisonExpression: visitar left y después right → `_check_condition`
- condición que no es comparación: registrar SEM004 → `_check_condition`
- IdentifierExpression: SEM001 o SEM003 → `_visit_expression`
- BinaryExpression: visitar left y después right → `_visit_expression`
- crear un Symbol con el siguiente id, o devolver None si el nombre existe → `SymbolTable.declare`
- reemplazar la entrada por una copia con initialized=True → `SymbolTable.mark_initialized`

Secuencia de visitas definida por el grupo para `int t = 2; t = (t - 1) + t;`:

```text
1. entrar a VariableDeclaration t
2. entrar a IntegerLiteral 2
3. declarar t
4. entrar a Assignment t
5. entrar a BinaryExpression +
6. entrar a BinaryExpression -
7. entrar a IdentifierExpression t
8. entrar a IntegerLiteral 1
9. entrar a IdentifierExpression t
10. marcar t inicializada
```

## 4. Casos de prueba que el agente debe verificar

Con `compile_source(fuente, stages=("lexer", "parser", "semantic"))` (requiere el lexer y el parser de los proyectos anteriores):

```c
x = 1;
int x;
x = 2;
```
→ SEM001 1:1

```c
int x = x;
```
→ SEM001 1:9

```c
int x;
int x = x;
```
→ SEM003 2:9, SEM002 2:1

```c
int x;
while (x != 0) {
    x = 1;
}
```
→ SEM003 2:8

```c
int a = 1;
while (a != 0) {
    int a = 0;
}
```
→ SEM002 3:5

```c
int x = 1;
int y = x;
```
→ sin diagnósticos

```c
x = y + z;
```
→ en este orden: SEM001 'y' 1:5 · SEM001 'z' 1:9 · SEM001 'x' 1:1

```c
int b;
b = b + w;
int b = q;
```
→ en este orden: SEM003 'b' 2:5 · SEM001 'w' 2:9 · SEM001 'q' 3:9 · SEM002 'b' 3:1

```c
int x;
int x = x;
x = 1;
int y = x;
z = y;
```
→ diagnósticos: SEM003 2:9, SEM002 2:1, SEM001 5:1
→ symbols:
```text
Symbol(1, 'x', 'INT', True, 1)
Symbol(2, 'y', 'INT', True, 4)
```

```c
int a;
int b = a;
a = 2;
int a = b;
c = a + b;
```
→ symbols:
```text
Symbol(1, 'a', 'INT', True, 1)
Symbol(2, 'b', 'INT', True, 2)
```

SEM004 se prueba **sin el parser**, construyendo el AST a mano:

```python
from minic.semantic import SemanticAnalyzer
from minic.syntax_tree import Assignment, IdentifierExpression, IntegerLiteral, Program, WhileStatement

condition = IntegerLiteral(0, line=1, column=8)
assignment = Assignment("w", IdentifierExpression("w", line=2, column=9),
                        line=2, column=5)
loop = WhileStatement(condition, (assignment,), line=1, column=1)
program = Program((loop,), line=1, column=1)
symbols, diagnostics = SemanticAnalyzer(program).analyze()
```
→ diagnósticos en orden: SEM004 1:8 · SEM001 'w' 2:9 · SEM001 'w' 2:5; symbols = []

Productos de `compile_source` según el grupo:

| Fuente | stages | Etapas ejecutadas | program | symbols | Primer diagnóstico |
|---|---|---|---|---|---|
| `x = 1;` | valor predeterminado | solo lexer | None | None | ninguno |
| `int x = @;` | las tres | solo lexer | None | None | LEX001 1:9 |
| `int x = 1\nint y = 2;` | las tres | lexer y parser | Program | None | SYN001 2:1 |
| `x = 1;` | las tres | las tres | Program | [] | SEM001 1:1 |
| `(vacía)` | las tres | las tres | Program | [] | ninguno |
| `int a = 1;\na = a + 1;` | las tres | las tres | Program | lista con símbolos | ninguno |

## 5. Instrucciones para el agente

1. Lee primero los dos esqueletos, `symbol.py`, `semantic_result.py`, `diagnostics/diagnostic_code.py`, `diagnostics/diagnostic_bag.py` y los nodos de `syntax_tree/`; **solo lectura** fuera de los dos archivos permitidos.
2. Implementa `SymbolTable` y luego `SemanticAnalyzer` siguiendo las secciones 1–3.
3. Ejecuta los casos de la sección 4 y compara diagnósticos (código, línea, columna y orden) y símbolos (los cinco campos). Si difieren, informa qué regla de esta especificación produce la diferencia en lugar de cambiarla por tu cuenta.
4. Corre `python -m pytest`. **No modifiques ninguna prueba.** Es esperado que falle `test_semantic_analyzer_is_stub` (exige que la etapa siga sin implementar) y, si las etapas anteriores ya existen, `test_lexer_is_stub`, `test_parser_is_stub` y la prueba de la CLI que espera el código 3; repórtalas como esperadas. Cualquier otra falla es un error tuyo. `tests/semantic/` puede no tener pruebas: tu verificación son los casos de la sección 4.
5. Si la especificación del grupo contradice el contrato del proyecto (por ejemplo, un orden de diagnósticos imposible), señálalo antes de continuar.