"""Safe arithmetic expression evaluator for benchmark value formulas.

Replaces eval(): parses the formula with ``ast`` and walks a strict
whitelist of node types. Anything else — attribute access, arbitrary
calls, names outside the known variable set, subscripts, comprehensions,
lambdas — is rejected before evaluation.

Allowed:
- variables: business_value, success_score, human_cost, latency_s,
  input_tokens, output_tokens (see ALLOWED_NAMES)
- numeric literals, arithmetic (+ - * / // % **), unary +/-,
  comparisons (== != < <= > >=), boolean ops (and or not),
  ternary (a if cond else b)
- calls to min / max / abs / round only
"""

import ast
from typing import Any


class FormulaError(ValueError):
    """Raised when a value formula is unsafe or invalid."""


# Names available inside value formulas. Extend carefully — each name
# must be supplied by the evaluation context (see BusinessValueCalculator).
ALLOWED_NAMES = frozenset({
    "business_value",
    "success_score",
    "human_cost",
    "latency_s",
    "input_tokens",
    "output_tokens",
})

ALLOWED_FUNCS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
}

_ALLOWED_NODES = (
    ast.Expression,
    # literals / names
    ast.Constant,
    ast.Name,
    # arithmetic
    ast.BinOp,
    ast.UnaryOp,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub,
    # comparison / boolean / ternary
    ast.Compare,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.BoolOp, ast.And, ast.Or, ast.Not,
    ast.IfExp,
    # whitelisted calls only
    ast.Call,
    ast.Load,
)


def _check_node(node: ast.AST) -> None:
    """Recursively validate that every node is on the whitelist."""
    for child in ast.walk(node):
        if not isinstance(child, _ALLOWED_NODES):
            raise FormulaError(
                f"forbidden syntax in formula: {type(child).__name__}"
            )
        if isinstance(child, ast.Name):
            if child.id not in ALLOWED_NAMES and child.id not in ALLOWED_FUNCS:
                raise FormulaError(f"unknown name in formula: {child.id!r}")
        elif isinstance(child, ast.Call):
            # Only bare calls to whitelisted functions: min(...), max(...)...
            if not (
                isinstance(child.func, ast.Name)
                and child.func.id in ALLOWED_FUNCS
            ):
                raise FormulaError("only min/max/abs/round calls are allowed")
            if child.keywords:
                raise FormulaError("keyword arguments are not allowed")
        elif isinstance(child, ast.Constant):
            # bool is a subclass of int — exclude it explicitly
            if isinstance(child.value, bool) or not isinstance(child.value, (int, float)):
                raise FormulaError("only numeric literals are allowed")


def validate_formula(formula: str) -> None:
    """Validate a formula string. Raises FormulaError if unsafe/invalid."""
    if not formula or not formula.strip():
        raise FormulaError("formula is empty")
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"syntax error: {exc.msg}") from exc
    _check_node(tree)


def safe_eval(formula: str, context: dict[str, Any]) -> float:
    """Evaluate a formula against a variable context.

    Raises FormulaError on unsafe formulas or evaluation failures
    (missing variable, division by zero, etc.).
    """
    validate_formula(formula)
    tree = ast.parse(formula, mode="eval")
    namespace = dict(ALLOWED_FUNCS)
    # Only expose known variables; missing ones raise NameError -> FormulaError
    for name in ALLOWED_NAMES:
        if name in context and context[name] is not None:
            namespace[name] = context[name]
    try:
        result = eval(  # noqa: S307 - AST is whitelisted above; no builtins
            compile(tree, "<formula>", "eval"),
            {"__builtins__": {}},
            namespace,
        )
    except FormulaError:
        raise
    except Exception as exc:
        raise FormulaError(f"evaluation failed: {exc}") from exc
    if not isinstance(result, (int, float)) or isinstance(result, bool):
        raise FormulaError(f"formula must return a number, got {type(result).__name__}")
    return float(result)
