from __future__ import annotations

import ast
import functools
from collections.abc import Iterable

from tokenize_rt import Offset

from .fold_nested_context_managers import _replace_context_managers
from pyupgrade._ast_helpers import ast_to_offset
from pyupgrade._data import register
from pyupgrade._data import State
from pyupgrade._data import TokenFunc


def _drop_underscore_names(items: list[ast.withitem]) -> list[ast.withitem]:
    """
    Remove unnecessary "_" names.

    Returns an empty list if there are no names that need changing.
    """
    transformed = []
    changed = False
    for item in items:
        if (
            isinstance(item.optional_vars, ast.Name) and
            item.optional_vars.id == '_'
        ):
            item.optional_vars = None
            changed = True
        transformed.append(item)

    if changed:
        return transformed

    return []


@register(ast.With)
def visit_With_drop_unnecessary_underscore_names(
    state: State,
    node: ast.With,
    parent: ast.AST,
) -> Iterable[tuple[Offset, TokenFunc]]:
    """
    Drop unnecessary _ names.

    If this is a with statement with multiple items, remove any `as _`.
    This was a work around before 3.10.

    with (foo as _, bar as _):
        body

    becomes

    with (foo, bar):
        body
    """
    if state.settings.min_version < (3, 10):
        return

    with_items = _drop_underscore_names(node.items)
    if with_items:
        yield ast_to_offset(node), functools.partial(
            _replace_context_managers,
            body=node.body,
            with_items=with_items,
        )
