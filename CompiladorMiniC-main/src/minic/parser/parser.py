"""Analizador sintáctico descendente recursivo de Mini C.

Se implementa en el **proyecto 2**. Hay un método por no terminal de la
gramática (SRS §14) y utilidades para recorrer los tokens.
"""

from minic.diagnostics import diagnostic_code
from minic.diagnostics.diagnostic_bag import DiagnosticBag
from minic.lexer.token import Token
from minic.lexer.token_type import TokenType
from minic.parser.parser_result import ParserResult
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


class Parser:
    """Convierte la lista de tokens en un AST.

    Uso: ``program, diagnostics = Parser(tokens).parse()``.
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Recibe los tokens del lexer, terminados en ``EOF``."""
        self._tokens = tokens
        self._current = 0
        self._diagnostics = DiagnosticBag()

    def parse(self) -> ParserResult:
        """Analiza el programa completo y devuelve el AST y los diagnósticos.

        Llama a ``parse_program`` y empaqueta el resultado.

        Devuelve:
            ``ParserResult(program, diagnostics)``.
        """
        program = self.parse_program()
        return ParserResult(program, self._diagnostics.to_list())

    # --- No terminales (SRS §14) -------------------------------------------

    def parse_program(self) -> Program:
        """``programa → instruccion* EOF``.

        Repite ``parse_statement`` hasta encontrar ``EOF``.
        """
        first_token = self.peek()
        statements: list[Statement] = []
        while not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return Program(tuple(statements), line=first_token.line, column=first_token.column)

    def parse_statement(self) -> Statement | None:
        """``instruccion → declaracion | asignacion | cicloWhile``.

        Decide por el token actual: ``KW_INT``, ``IDENTIFIER`` o ``KW_WHILE``.
        Devuelve ``None`` si no pudo reconocer una instrucción y tuvo que
        recuperarse.
        """
        if self.check(TokenType.KW_INT):
            return self.parse_declaration()
        if self.check(TokenType.IDENTIFIER):
            return self.parse_assignment()
        if self.check(TokenType.KW_WHILE):
            return self.parse_while()
        if not self.check(TokenType.EOF):
            self.advance()
        return None

    def parse_declaration(self) -> VariableDeclaration:
        """``declaracion → KW_INT IDENTIFIER ";" | KW_INT IDENTIFIER "=" expresion ";"``.

        Si falta ``;`` registra ``SYN001``.
        """
        int_token = self.advance()
        name_token = self.advance()
        name = name_token.lexeme
        if self.check(TokenType.ASSIGN):
            self.advance()
            initializer: Expression | None = self.parse_expression()
        else:
            initializer = None
        self.expect(
            TokenType.SEMICOLON,
            diagnostic_code.SYN001,
            diagnostic_code.expected_semicolon(),
        )
        return VariableDeclaration(
            name, initializer, line=int_token.line, column=int_token.column
        )

    def parse_assignment(self) -> Assignment:
        """``asignacion → IDENTIFIER "=" expresion ";"``.

        Si falta ``;`` registra ``SYN001``.
        """
        id_token = self.advance()
        self.advance()
        value = self.parse_expression()
        self.expect(
            TokenType.SEMICOLON,
            diagnostic_code.SYN001,
            diagnostic_code.expected_semicolon(),
        )
        return Assignment(id_token.lexeme, value, line=id_token.line, column=id_token.column)

    def parse_while(self) -> WhileStatement:
        """``cicloWhile → KW_WHILE "(" condicion ")" bloque``.

        Si falta ``)`` registra ``SYN002``.
        """
        while_token = self.advance()
        self.advance()
        condition = self.parse_condition()
        self.expect(
            TokenType.RPAREN,
            diagnostic_code.SYN002,
            diagnostic_code.expected_right_paren(),
        )
        body = self.parse_block()
        return WhileStatement(
            condition, body, line=while_token.line, column=while_token.column
        )

    def parse_block(self) -> tuple[Statement, ...]:
        """``bloque → "{" instruccion* "}"``.

        Si falta ``}`` registra ``SYN003``.
        """
        self.advance()
        statements: list[Statement] = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                statements.append(stmt)
        self.expect(
            TokenType.RBRACE,
            diagnostic_code.SYN003,
            diagnostic_code.expected_right_brace(),
        )
        return tuple(statements)

    def parse_condition(self) -> Expression:
        """``condicion → expresion ("==" | "!=") expresion``.

        Devuelve una ``ComparisonExpression``. ``==`` y ``!=`` tienen menor
        precedencia que ``+`` y ``-``.
        """
        left = self.parse_expression()
        op_token = self.advance()
        right = self.parse_expression()
        return ComparisonExpression(
            left, op_token.lexeme, right, line=left.line, column=left.column
        )

    def parse_expression(self) -> Expression:
        """``expresion → termino (("+" | "-") termino)*``.

        Construye ``BinaryExpression`` asociando a la izquierda:
        ``a - b - c`` equivale a ``(a - b) - c``.
        """
        expr = self.parse_term()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_term()
            expr = BinaryExpression(
                expr, op_token.lexeme, right, line=expr.line, column=expr.column
            )
        return expr

    def parse_term(self) -> Expression:
        """``termino → INTEGER_LITERAL | IDENTIFIER | "(" expresion ")"``.

        Si falta el ``)`` de cierre registra ``SYN002``.
        """
        if self.check(TokenType.INTEGER_LITERAL):
            token = self.advance()
            value = token.literal if token.literal is not None else int(token.lexeme)
            return IntegerLiteral(value, line=token.line, column=token.column)
        if self.check(TokenType.IDENTIFIER):
            token = self.advance()
            return IdentifierExpression(token.lexeme, line=token.line, column=token.column)
        if self.check(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(
                TokenType.RPAREN,
                diagnostic_code.SYN002,
                diagnostic_code.expected_right_paren(),
            )
            return expr
        token = self.advance()
        return IntegerLiteral(0, line=token.line, column=token.column)

    # --- Utilidades --------------------------------------------------------

    def peek(self) -> Token:
        """Devuelve el token actual sin consumirlo."""
        if not self._tokens:
            return Token(TokenType.EOF, "", None, 1, 1)
        if self._current < len(self._tokens):
            return self._tokens[self._current]
        return self._tokens[-1]

    def advance(self) -> Token:
        """Consume y devuelve el token actual; nunca avanza más allá de ``EOF``."""
        token = self.peek()
        if token.type != TokenType.EOF:
            self._current += 1
        return token

    def check(self, token_type: str) -> bool:
        """Indica si el token actual es de tipo ``token_type``, sin consumirlo."""
        return self.peek().type == token_type

    def expect(self, token_type: str, code: str, message: str) -> Token | None:
        """Consume el token si es de tipo ``token_type``.

        Si no lo es, registra el diagnóstico ``code`` con ``message`` en la
        posición del token actual y devuelve ``None`` sin detener el análisis.
        """
        if self.check(token_type):
            return self.advance()
        token = self.peek()
        self._diagnostics.report(code, message, token.line, token.column)
        return None
