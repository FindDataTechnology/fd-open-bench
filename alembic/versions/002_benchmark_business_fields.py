"""benchmark entity + golden business fields + run batch columns

Revision ID: 002
Revises: 001
Create Date: 2026-08-08

Changes:
- create benchmarks table (题+尺+生意: dataset + metric_suite + value model)
- goldens: rename metadata -> extra_metadata (fix model/migration mismatch from 001),
  business_value JSON -> Numeric(12,2), add human_cost / human_minutes,
  backfill business_value from extra_metadata.business_value
- evaluation_runs: add benchmark_id (FK, SET NULL) and batch_id with indexes
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- benchmarks table ---
    op.create_table(
        "benchmarks",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("metric_suite", sa.JSON(), nullable=False),
        sa.Column("value_formula", sa.Text(), nullable=True),
        sa.Column("time_value_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.ForeignKeyConstraint(
            ["dataset_id"], ["datasets.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("idx_benchmark_name", "benchmarks", ["name"], unique=True)

    # --- goldens: business columns ---
    with op.batch_alter_table("goldens") as batch_op:
        batch_op.alter_column("metadata", new_column_name="extra_metadata")
        batch_op.alter_column(
            "business_value",
            existing_type=sa.JSON(),
            type_=sa.Numeric(12, 2),
            existing_nullable=True,
            postgresql_using="nullif(trim(both '\"' from business_value::text), 'null')::numeric(12,2)",
        )
        batch_op.add_column(sa.Column("human_cost", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(sa.Column("human_minutes", sa.Integer(), nullable=True))

    # Backfill business_value from extra_metadata.business_value where unset
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute(
            """
            UPDATE goldens
            SET business_value = CAST(json_extract(extra_metadata, '$.business_value') AS NUMERIC)
            WHERE business_value IS NULL
              AND json_type(extra_metadata, '$.business_value') IN ('integer', 'real')
            """
        )
    elif bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE goldens
            SET business_value = (extra_metadata->>'business_value')::numeric
            WHERE business_value IS NULL
              AND jsonb_typeof(extra_metadata::jsonb, 'business_value') IN ('number')
            """
        )

    # --- evaluation_runs: benchmark / batch columns ---
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.add_column(sa.Column("benchmark_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("batch_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_run_benchmark", "benchmarks", ["benchmark_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index("idx_run_batch", ["batch_id"])
        batch_op.create_index("idx_run_benchmark", ["benchmark_id"])


def downgrade() -> None:
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.drop_index("idx_run_benchmark")
        batch_op.drop_index("idx_run_batch")
        batch_op.drop_constraint("fk_run_benchmark", type_="foreignkey")
        batch_op.drop_column("batch_id")
        batch_op.drop_column("benchmark_id")

    with op.batch_alter_table("goldens") as batch_op:
        batch_op.drop_column("human_minutes")
        batch_op.drop_column("human_cost")
        batch_op.alter_column(
            "business_value",
            existing_type=sa.Numeric(12, 2),
            type_=sa.JSON(),
            existing_nullable=True,
        )
        batch_op.alter_column("extra_metadata", new_column_name="metadata")

    op.drop_index("idx_benchmark_name", table_name="benchmarks")
    op.drop_table("benchmarks")
