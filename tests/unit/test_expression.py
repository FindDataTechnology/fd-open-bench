"""Unit tests for the safe formula evaluator (app/utils/expression.py)."""

import pytest

from app.utils.expression import FormulaError, safe_eval, validate_formula


CTX = {
    "business_value": 100.0,
    "success_score": 0.8,
    "human_cost": 25.0,
    "latency_s": 12.5,
    "input_tokens": 1500,
    "output_tokens": 300,
}


class TestValidFormulas:
    def test_default_formula(self):
        assert safe_eval("business_value * success_score", CTX) == pytest.approx(80.0)

    def test_arithmetic_and_constants(self):
        assert safe_eval("business_value * success_score - latency_s * 0.5", CTX) == pytest.approx(73.75)

    def test_ternary(self):
        assert safe_eval("business_value if success_score > 0.5 else 0", CTX) == 100.0
        assert safe_eval("business_value if success_score > 0.9 else 0", CTX) == 0.0

    def test_whitelisted_funcs(self):
        assert safe_eval("min(business_value, human_cost * 3)", CTX) == 75.0
        assert safe_eval("max(0, business_value - human_cost)", CTX) == 75.0
        assert safe_eval("abs(human_cost - business_value)", CTX) == 75.0
        assert safe_eval("round(business_value * success_score / 3, 1)", CTX) == pytest.approx(26.7)

    def test_comparison_in_ternary(self):
        assert safe_eval("1 if input_tokens + output_tokens > 1000 else 2", CTX) == 1.0

    def test_human_replacement_ratio(self):
        assert safe_eval("human_cost / (business_value * 0.01)", CTX) == 25.0

    def test_mod_floordiv_pow(self):
        assert safe_eval("output_tokens % 7 + input_tokens // 1000 + 2 ** 3", CTX) == float(300 % 7 + 1 + 8)


class TestRejectedPayloads:
    @pytest.mark.parametrize("payload", [
        "__class__",
        "business_value.__class__",
        "().__class__.__bases__[0].__subclasses__()",
        "import os",
        "open('/etc/passwd').read()",
        "exec('1')",
        "eval('1+1')",
        "print('hi')",
        "business_value.real",
        "[x for x in range(10)]",
        "lambda x: x",
        "ctx['business_value']",
        "os.system('ls')",
        "min.__globals__",
        "f'{business_value}'",
        "True",
        "'string'",
        "unknown_var + 1",
        "min(1, 2, key=abs)",
    ])
    def test_payload_rejected(self, payload):
        with pytest.raises(FormulaError):
            safe_eval(payload, CTX)

    def test_validate_syntax_error(self):
        with pytest.raises(FormulaError):
            validate_formula("business_value *")

    def test_validate_empty(self):
        with pytest.raises(FormulaError):
            validate_formula("   ")


class TestEvaluationFailures:
    def test_missing_variable(self):
        with pytest.raises(FormulaError):
            safe_eval("business_value * success_score", {"business_value": 1.0})

    def test_none_variable_treated_as_missing(self):
        ctx = dict(CTX, success_score=None)
        with pytest.raises(FormulaError):
            safe_eval("business_value * success_score", ctx)

    def test_division_by_zero(self):
        with pytest.raises(FormulaError):
            safe_eval("business_value / (success_score - 0.8)", CTX)

    def test_bool_result_rejected(self):
        with pytest.raises(FormulaError):
            safe_eval("success_score > 0.5", CTX)
