from typing import Any
from decimal import Decimal
from app.utils.expression import safe_eval, FormulaError


class BusinessValueCalculator:
    """Calculate business value and ROI for evaluations."""

    def __init__(self, business_model: dict[str, Any] | None = None):
        self.model = business_model or {}
        self.pricing_config = self.model.get("pricing_config", {})
        self.value_formula = self.model.get("value_formula", "")
        self.roi_targets = self.model.get("roi_targets", {})

    def calculate_token_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o",
    ) -> Decimal:
        """Calculate cost based on token usage."""
        # Default pricing for gpt-4o
        pricing = self.pricing_config.get("token_pricing", {}).get(model, {
            "input_per_1k": 0.0025,
            "output_per_1k": 0.01,
        })

        input_cost = Decimal(str(input_tokens)) / Decimal("1000") * Decimal(str(pricing["input_per_1k"]))
        output_cost = Decimal(str(output_tokens)) / Decimal("1000") * Decimal(str(pricing["output_per_1k"]))

        return input_cost + output_cost

    def calculate_time_cost(
        self,
        execution_time_ms: int,
        pricing_type: str = "per_minute",
    ) -> Decimal:
        """Calculate cost based on execution time."""
        time_pricing = self.pricing_config.get("time_pricing", {})

        if pricing_type == "per_minute":
            rate = Decimal(str(time_pricing.get("per_minute", 0.10)))
            minutes = Decimal(str(execution_time_ms)) / Decimal("60000")
            return minutes * rate
        elif pricing_type == "per_hour":
            rate = Decimal(str(time_pricing.get("per_hour", 6.0)))
            hours = Decimal(str(execution_time_ms)) / Decimal("3600000")
            return hours * rate
        else:
            return Decimal("0")

    def calculate_business_value(
        self,
        task_completed: bool,
        success_score: float,
        golden_metadata: dict[str, Any],
    ) -> Decimal:
        """Calculate business value delivered."""
        if not task_completed:
            return Decimal("0")

        # If custom formula, evaluate it with safe evaluator
        if self.value_formula:
            try:
                context = {
                    "success_score": success_score,
                    "business_value": golden_metadata.get("business_value", 100),
                    "human_cost": golden_metadata.get("human_cost", 50),
                    "latency_s": golden_metadata.get("latency_s", 10),
                    "input_tokens": golden_metadata.get("input_tokens", 1000),
                    "output_tokens": golden_metadata.get("output_tokens", 200),
                }
                result = safe_eval(self.value_formula, context)
                return Decimal(str(result))
            except FormulaError as e:
                # Fallback to default formula on error
                # Log the error (in production, this would use proper logging)
                print(f"Formula evaluation failed: {e}, using fallback")
                base_value = Decimal(str(golden_metadata.get("business_value", 100)))
                return base_value * Decimal(str(success_score))

        # Default: use business_value from golden or default
        base_value = Decimal(str(golden_metadata.get("business_value", 100)))
        return base_value * Decimal(str(success_score))

    def calculate_roi(
        self,
        business_value: Decimal,
        total_cost: Decimal,
    ) -> float:
        """Calculate ROI (Return on Investment)."""
        if total_cost == 0:
            return 0.0

        roi = (business_value - total_cost) / total_cost * Decimal("100")
        return float(roi)

    def calculate_cost_efficiency(
        self,
        business_value: Decimal,
        total_cost: Decimal,
    ) -> float:
        """Calculate cost efficiency (value per dollar)."""
        if total_cost == 0:
            return 0.0

        efficiency = business_value / total_cost
        return float(efficiency)

    def check_cost_alert(self, cost_per_task: Decimal) -> dict[str, Any] | None:
        """Check if cost alert should be triggered."""
        alerts = self.model.get("cost_alerts", {})
        threshold = Decimal(str(alerts.get("threshold", 1.0)))
        metric = alerts.get("metric", "cost_per_task")

        if metric == "cost_per_task" and cost_per_task > threshold:
            return {
                "triggered": True,
                "metric": metric,
                "value": float(cost_per_task),
                "threshold": float(threshold),
                "message": f"Cost per task (${float(cost_per_task):.2f}) exceeds threshold (${float(threshold):.2f})",
            }

        return None

    def what_if_analysis(
        self,
        current_pricing: str,
        alternative_pricing: str,
        avg_tokens_per_task: int,
        avg_time_per_task_ms: int,
    ) -> dict[str, Any]:
        """Compare costs between different pricing models."""
        # Current cost
        if current_pricing == "tokens":
            current_cost = self.calculate_token_cost(
                avg_tokens_per_task // 2,
                avg_tokens_per_task // 2,
            )
        else:
            current_cost = self.calculate_time_cost(avg_time_per_task_ms, current_pricing)

        # Alternative cost
        if alternative_pricing == "tokens":
            alt_cost = self.calculate_token_cost(
                avg_tokens_per_task // 2,
                avg_tokens_per_task // 2,
            )
        else:
            alt_cost = self.calculate_time_cost(avg_time_per_task_ms, alternative_pricing)

        return {
            "current_pricing": current_pricing,
            "current_cost": float(current_cost),
            "alternative_pricing": alternative_pricing,
            "alternative_cost": float(alt_cost),
            "savings": float(current_cost - alt_cost),
            "recommendation": "switch" if alt_cost < current_cost else "keep_current",
        }
