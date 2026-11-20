"""Tabla de símbolos de Mini C.

Se implementa en el **proyecto 3** (SRS §17–18). Como ``Symbol`` es inmutable,
marcar una variable como inicializada reemplaza su entrada por una copia.
"""

import dataclasses

from minic.semantic.symbol import Symbol


class SymbolTable:
    """Registra las variables declaradas y su estado de inicialización."""

    def __init__(self) -> None:
        self._symbols: dict[str, Symbol] = {}
        self._next_id: int = 1

    def declare(self, name: str, declared_line: int, initialized: bool) -> Symbol | None:
        """Declara ``name`` con tipo ``"INT"`` y el siguiente ``id`` disponible.

        Devuelve el ``Symbol`` creado, o ``None`` si ``name`` ya estaba
        declarado en el mismo ámbito (el analizador reporta ``SEM002``).
        """
        if name in self._symbols:
            return None
        symbol = Symbol(
            id=self._next_id,
            name=name,
            type="INT",
            initialized=initialized,
            declared_line=declared_line,
        )
        self._symbols[name] = symbol
        self._next_id += 1
        return symbol

    def lookup(self, name: str) -> Symbol | None:
        """Busca ``name``; devuelve su ``Symbol`` o ``None`` si no fue declarado."""
        return self._symbols.get(name)

    def mark_initialized(self, name: str) -> Symbol:
        """Reemplaza la entrada de ``name`` por una copia con ``initialized=True``.

        Precondición: ``name`` fue declarado. Devuelve el símbolo actualizado.
        """
        if name not in self._symbols:
            raise KeyError(f"Variable no declarada: '{name}'")
        symbol = dataclasses.replace(self._symbols[name], initialized=True)
        self._symbols[name] = symbol
        return symbol

    def symbols(self) -> list[Symbol]:
        """Devuelve los símbolos en orden de declaración (por ``id``)."""
        return sorted(self._symbols.values(), key=lambda s: s.id)
