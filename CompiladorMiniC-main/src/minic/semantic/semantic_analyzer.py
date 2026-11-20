"""Analizador semántico de Mini C.

Se implementa en el **proyecto 3**. Recorre el AST y aplica las reglas de la
SRS §17–18 con ayuda de ``SymbolTable``.
"""

from minic.diagnostics import diagnostic_code
from minic.diagnostics.diagnostic_bag import DiagnosticBag
from minic.semantic.semantic_result import SemanticResult
from minic.semantic.symbol_table import SymbolTable
from minic.syntax_tree.expressions import (
    BinaryExpression,
    ComparisonExpression,
    Expression,
    IdentifierExpression,
    IntegerLiteral,
)
from minic.syntax_tree.program import Program
from minic.syntax_tree.statements import (
    Assignment,
    Statement,
    VariableDeclaration,
    WhileStatement,
)


class SemanticAnalyzer:
    """Verifica las reglas semánticas de un programa ya analizado.

    Uso: ``symbols, diagnostics = SemanticAnalyzer(program).analyze()``.
    """

    def __init__(self, program: Program) -> None:
        """Recibe la raíz del AST producida por el parser."""
        self._program = program
        self._table = SymbolTable()
        self._diagnostics = DiagnosticBag()

    def analyze(self) -> SemanticResult:
        """Recorre todas las instrucciones del programa y devuelve el resultado.

        Devuelve:
            ``SemanticResult(symbols, diagnostics)``.
        """
        for statement in self._program.statements:
            self._visit_statement(statement)
        return SemanticResult(self._table.symbols(), self._diagnostics.to_list())

    def _visit_statement(self, statement: Statement) -> None:
        """Despacha según el tipo concreto de instrucción."""
        if isinstance(statement, VariableDeclaration):
            self._visit_declaration(statement)
        elif isinstance(statement, Assignment):
            self._visit_assignment(statement)
        elif isinstance(statement, WhileStatement):
            self._visit_while(statement)

    def _visit_declaration(self, node: VariableDeclaration) -> None:
        """Verifica el inicializador (si existe) y declara la variable.

        Redeclarar en el mismo ámbito registra ``SEM002``.
        """
        if node.initializer is not None:
            self._visit_expression(node.initializer)
        symbol = self._table.declare(node.name, node.line, node.initializer is not None)
        if symbol is None:
            self._diagnostics.report(
                diagnostic_code.SEM002,
                diagnostic_code.redeclared_variable(node.name),
                node.line,
                node.column,
            )

    def _visit_assignment(self, node: Assignment) -> None:
        """Verifica el valor y marca la variable como inicializada.

        Asignar a una variable no declarada registra ``SEM001``.
        """
        self._visit_expression(node.value)
        symbol = self._table.lookup(node.name)
        if symbol is None:
            self._diagnostics.report(
                diagnostic_code.SEM001,
                diagnostic_code.undeclared_variable(node.name),
                node.line,
                node.column,
            )
        else:
            self._table.mark_initialized(node.name)

    def _visit_while(self, node: WhileStatement) -> None:
        """Verifica la condición con ``_check_condition`` y luego el cuerpo."""
        self._check_condition(node.condition)
        for statement in node.body:
            self._visit_statement(statement)

    def _check_condition(self, condition: Expression) -> None:
        """Exige que la condición del ``while`` sea una ``ComparisonExpression``.

        Si no lo es registra ``SEM004``. Luego verifica ambos lados.
        """
        if isinstance(condition, ComparisonExpression):
            self._visit_expression(condition.left)
            self._visit_expression(condition.right)
        else:
            self._diagnostics.report(
                diagnostic_code.SEM004,
                diagnostic_code.invalid_operation("la condición de 'while' debe ser una comparación"),
                condition.line,
                condition.column,
            )
            self._visit_expression(condition)

    def _visit_expression(self, expression: Expression) -> None:
        """Verifica cada lectura de variable dentro de la expresión.

        Variable no declarada: ``SEM001``. Declarada pero sin valor: ``SEM003``.
        """
        if isinstance(expression, IdentifierExpression):
            symbol = self._table.lookup(expression.name)
            if symbol is None:
                self._diagnostics.report(
                    diagnostic_code.SEM001,
                    diagnostic_code.undeclared_variable(expression.name),
                    expression.line,
                    expression.column,
                )
            elif not symbol.initialized:
                self._diagnostics.report(
                    diagnostic_code.SEM003,
                    diagnostic_code.uninitialized_variable(expression.name),
                    expression.line,
                    expression.column,
                )
        elif isinstance(expression, BinaryExpression):
            self._visit_expression(expression.left)
            self._visit_expression(expression.right)
        elif isinstance(expression, ComparisonExpression):
            self._visit_expression(expression.left)
            self._visit_expression(expression.right)
        elif isinstance(expression, IntegerLiteral):
            pass
