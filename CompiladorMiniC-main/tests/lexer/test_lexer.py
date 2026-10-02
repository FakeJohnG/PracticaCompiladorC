"""Pruebas del analizador léxico de Mini C.

Verifica la especificación completa de la skill analizador-lexico-mini-c y el
capítulo IV, §4.4.
"""

from minic.diagnostics.diagnostic_code import LEX001
from minic.lexer import Lexer, Token, TokenType
from minic.output import format_diagnostic, format_token


def test_section7_valid_source() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []

    expected = [
        Token(TokenType.IDENTIFIER, "int2", None, 1, 1),
        Token(TokenType.ASSIGN, "=", None, 1, 6),
        Token(TokenType.INTEGER_LITERAL, "12", 12, 1, 8),
        Token(TokenType.IDENTIFIER, "abc", None, 1, 10),
        Token(TokenType.SEMICOLON, ";", None, 1, 13),
        Token(TokenType.IDENTIFIER, "whilex", None, 2, 1),
        Token(TokenType.EQUAL_EQUAL, "==", None, 2, 8),
        Token(TokenType.MINUS, "-", None, 2, 11),
        Token(TokenType.INTEGER_LITERAL, "5", 5, 2, 12),
        Token(TokenType.EOF, "", None, 2, 13),
    ]

    assert tokens == expected


def test_section7_source_with_errors() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    tokens, diagnostics = Lexer(source).scan()

    expected_tokens = [
        Token(TokenType.KW_INT, "int", None, 1, 1),
        Token(TokenType.IDENTIFIER, "x", None, 1, 5),
        Token(TokenType.ASSIGN, "=", None, 1, 7),
        Token(TokenType.SEMICOLON, ";", None, 1, 10),
        Token(TokenType.IDENTIFIER, "x", None, 2, 1),
        Token(TokenType.ASSIGN, "=", None, 2, 5),
        Token(TokenType.INTEGER_LITERAL, "0", 0, 2, 7),
        Token(TokenType.SEMICOLON, ";", None, 2, 8),
        Token(TokenType.IDENTIFIER, "fin", None, 2, 13),
        Token(TokenType.EOF, "", None, 2, 16),
    ]

    assert tokens == expected_tokens

    formatted_diagnostics = [format_diagnostic(d) for d in diagnostics]
    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]
    assert formatted_diagnostics == expected_diagnostics


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert diagnostics == []
    assert tokens == [Token(TokenType.EOF, "", None, 1, 1)]


def test_keywords_and_identifiers() -> None:
    source = "int while int_ while1 _int whilex int2"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.KW_INT,
        TokenType.KW_WHILE,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
    ]


def test_operators_and_delimiters() -> None:
    source = "= == != + - ( ) { } ;"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.ASSIGN,
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
    ]


def test_number_literal_values() -> None:
    source = "0 007 42 1234567890"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    literals = [t.literal for t in tokens[:-1]]
    assert literals == [0, 7, 42, 1234567890]
    lexemes = [t.lexeme for t in tokens[:-1]]
    assert lexemes == ["0", "007", "42", "1234567890"]


def test_whitespace_and_tabs() -> None:
    # \t cuenta como 1 columna
    source = "a\tb\n\tc"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    assert tokens[0] == Token(TokenType.IDENTIFIER, "a", None, 1, 1)
    assert tokens[1] == Token(TokenType.IDENTIFIER, "b", None, 1, 3)
    assert tokens[2] == Token(TokenType.IDENTIFIER, "c", None, 2, 2)


def test_carriage_return_alone() -> None:
    # \r solo es un blanco que suma 1 columna, no abre línea
    source = "a\rb"
    tokens, diagnostics = Lexer(source).scan()
    assert diagnostics == []
    assert tokens[0] == Token(TokenType.IDENTIFIER, "a", None, 1, 1)
    assert tokens[1] == Token(TokenType.IDENTIFIER, "b", None, 1, 3)


def test_unrecognized_characters_recovery() -> None:
    source = "$var # 12"
    tokens, diagnostics = Lexer(source).scan()
    assert len(diagnostics) == 2
    assert diagnostics[0].code == LEX001
    assert diagnostics[0].message == "Carácter no reconocido: '$'"
    assert diagnostics[0].line == 1
    assert diagnostics[0].column == 1

    assert diagnostics[1].code == LEX001
    assert diagnostics[1].message == "Carácter no reconocido: '#'"
    assert diagnostics[1].line == 1
    assert diagnostics[1].column == 6

    # Los tokens válidos siguen produciéndose hasta EOF
    assert tokens == [
        Token(TokenType.IDENTIFIER, "var", None, 1, 2),
        Token(TokenType.INTEGER_LITERAL, "12", 12, 1, 8),
        Token(TokenType.EOF, "", None, 1, 10),
    ]


def test_format_token_output() -> None:
    token = Token(TokenType.KW_INT, "int", None, 1, 1)
    assert format_token(token) == "KW_INT 'int' 1 1"
    eof = Token(TokenType.EOF, "", None, 2, 5)
    assert format_token(eof) == "EOF '' 2 5"
