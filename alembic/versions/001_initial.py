"""initial

Revision ID: 001
Revises:
Create Date: 2025-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("adapter_type", sa.String(50), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("pricing_config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_agent_name", "agents", ["name"], unique=True)

    # Datasets table
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_dataset_name", "datasets", ["name"], unique=True)

    # Goldens table
    op.create_table(
        "goldens",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("expected_tools", sa.JSON(), nullable=True),
        sa.Column("business_value", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_golden_dataset", "goldens", ["dataset_id"])
    op.create_index("idx_golden_created", "goldens", ["created_at"])

    # EvaluationRuns table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("evaluation_config", sa.JSON(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "PARTIALLY_COMPLETED", name="evaluationrunstatus"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("tasks_total", sa.Integer(), nullable=False),
        sa.Column("tasks_completed", sa.Integer(), nullable=False),
        sa.Column("tasks_failed", sa.Integer(), nullable=False),
        sa.Column("current_cost", sa.String(50), nullable=False),
        sa.Column("results_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_run_agent_created", "evaluation_runs", ["agent_id", "created_at"])
    op.create_index("idx_run_status_created", "evaluation_runs", ["status", "created_at"])

    # EvaluationResults table
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("golden_id", sa.String(36), nullable=False),
        sa.Column("agent_output", sa.Text(), nullable=True),
        sa.Column("trace", sa.JSON(), nullable=True),
        sa.Column("token_usage", sa.JSON(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("metric_scores", sa.JSON(), nullable=False),
        sa.Column("validator_results", sa.JSON(), nullable=False),
        sa.Column("business_value_delivered", sa.String(50), nullable=True),
        sa.Column("total_cost", sa.String(50), nullable=True),
        sa.Column("status", sa.Enum("SUCCESS", "FAILED", "TIMEOUT", "ERROR", name="evaluationresultstatus"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["evaluation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["golden_id"],
            ["goldens.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_result_run_status", "evaluation_results", ["run_id", "status"])
    op.create_index("idx_result_run_created", "evaluation_results", ["run_id", "created_at"])

    # BusinessModels table
    op.create_table(
        "business_models",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), nullable=False),
        sa.Column("pricing_config", sa.JSON(), nullable=False),
        sa.Column("value_formula", sa.Text(), nullable=True),
        sa.Column("roi_targets", sa.JSON(), nullable=False),
        sa.Column("cost_alerts", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id"),
    )
    op.create_index("idx_business_model_agent", "business_models", ["agent_id"], unique=True)

    # EvaluatorConfigs table
    op.create_table(
        "evaluator_configs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_evaluator_name", "evaluator_configs", ["name"], unique=True)


def downgrade() -> None:
    op.drop_table("evaluator_configs")
    op.drop_table("business_models")
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("goldens")
    op.drop_table("datasets")
    op.drop_table("agents")
