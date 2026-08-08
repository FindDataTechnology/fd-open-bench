"""Unit tests for the comparison service."""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Agent, Dataset, Golden, Benchmark, EvaluationRun, EvaluationResult
from app.models.evaluation_run import EvaluationRunStatus
from app.models.evaluation_result import EvaluationResultStatus
from app.services.comparison import ComparisonService
import uuid


# Create in-memory SQLite database for testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing."""
    # Create dataset
    dataset = Dataset(
        id=str(uuid.uuid4()),
        name="Test Dataset",
        description="Test"
    )
    db_session.add(dataset)

    # Create benchmark
    benchmark = Benchmark(
        id=str(uuid.uuid4()),
        name="Test Benchmark",
        description="Test",
        dataset_id=dataset.id,
        metric_suite=["accuracy"],
        value_formula="business_value * success_score",
        time_value_rate=50.0
    )
    db_session.add(benchmark)

    # Create goldens with business values
    goldens = []
    for i in range(3):
        golden = Golden(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            input=f"Task {i}",
            expected_output=f"Output {i}",
            business_value=Decimal("100.00"),
            human_cost=Decimal("50.00"),
            human_minutes=10
        )
        db_session.add(golden)
        goldens.append(golden)

    # Create agents
    agent_a = Agent(
        id=str(uuid.uuid4()),
        name="Agent A",
        description="Test Agent A",
        adapter_type="custom",
        config={},
        pricing_config={}
    )
    agent_b = Agent(
        id=str(uuid.uuid4()),
        name="Agent B",
        description="Test Agent B",
        adapter_type="custom",
        config={},
        pricing_config={}
    )
    db_session.add(agent_a)
    db_session.add(agent_b)

    db_session.commit()

    return {
        "dataset": dataset,
        "benchmark": benchmark,
        "goldens": goldens,
        "agent_a": agent_a,
        "agent_b": agent_b,
    }


def create_evaluation_run(db_session, agent, benchmark, status=EvaluationRunStatus.COMPLETED.value):
    """Helper to create an evaluation run."""
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        agent_id=agent.id,
        dataset_id=benchmark.dataset_id,
        benchmark_id=benchmark.id,
        status=status,
        tasks_total=3,
        tasks_completed=3,
        tasks_failed=0,
        current_cost=10.0,
        evaluation_config={}
    )
    db_session.add(run)
    db_session.commit()
    return run


def create_evaluation_result(db_session, run, golden, metric_scores, status=EvaluationResultStatus.SUCCESS):
    """Helper to create an evaluation result."""
    result = EvaluationResult(
        id=str(uuid.uuid4()),
        run_id=run.id,
        golden_id=golden.id,
        metric_scores=metric_scores,
        total_cost="1.0",
        execution_time_ms=1000,
        status=status,
        business_value_delivered="100.0"
    )
    db_session.add(result)
    db_session.commit()
    return result


class TestComparisonService:
    def test_cost_per_success_calculation(self, db_session, sample_data):
        """Test that cost_per_success is calculated correctly."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Create a run with successful results
        run = create_evaluation_run(db_session, agent, benchmark)

        # Create results: 2 successful, 1 failed
        create_evaluation_result(db_session, run, goldens[0], {"accuracy": 0.9})
        create_evaluation_result(db_session, run, goldens[1], {"accuracy": 0.8})
        create_evaluation_result(db_session, run, goldens[2], {"accuracy": 0.0}, status=EvaluationResultStatus.FAILED)

        # Calculate stats
        service = ComparisonService(db_session)
        stats = service._calculate_agent_stats(agent.id, [run], benchmark.time_value_rate)

        # cost_per_success = total_cost / success_count = 3.0 / 2 = 1.5
        assert stats["cost_per_success"] == 1.5
        assert stats["success_count"] == 2
        assert stats["task_count"] == 3

    def test_cost_per_success_zero_successes(self, db_session, sample_data):
        """Test that cost_per_success returns None when there are no successes."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Create a run with all failed results
        run = create_evaluation_run(db_session, agent, benchmark)

        for golden in goldens:
            create_evaluation_result(db_session, run, golden, {"accuracy": 0.0}, status=EvaluationResultStatus.FAILED)

        # Calculate stats
        service = ComparisonService(db_session)
        stats = service._calculate_agent_stats(agent.id, [run], benchmark.time_value_rate)

        assert stats["cost_per_success"] is None
        assert stats["success_count"] == 0

    def test_human_replacement_calculation(self, db_session, sample_data):
        """Test that human_replacement is calculated correctly."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Create a run with successful results
        run = create_evaluation_run(db_session, agent, benchmark)

        # All successful
        for golden in goldens:
            create_evaluation_result(db_session, run, golden, {"accuracy": 0.9})

        # Calculate stats
        service = ComparisonService(db_session)
        stats = service._calculate_agent_stats(agent.id, [run], benchmark.time_value_rate)

        # human_replacement = cost_per_success / avg_human_cost
        # cost_per_success = 3.0 / 3 = 1.0
        # avg_human_cost = 50.0
        # human_replacement = 1.0 / 50.0 = 0.02
        assert stats["human_replacement"] == pytest.approx(0.02)

    def test_time_cost_calculation(self, db_session, sample_data):
        """Test that time_cost is calculated correctly."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Create a run
        run = create_evaluation_run(db_session, agent, benchmark)

        # Create results with different latencies
        create_evaluation_result(db_session, run, goldens[0], {"accuracy": 0.9})  # 1s
        result2 = create_evaluation_result(db_session, run, goldens[1], {"accuracy": 0.8})
        result2.execution_time_ms = 2000  # 2s
        db_session.commit()

        # Calculate stats
        service = ComparisonService(db_session)
        stats = service._calculate_agent_stats(agent.id, [run], benchmark.time_value_rate)

        # total_time = 3s
        # time_cost = 3 * 50.0 / 3600 = 0.041666...
        assert stats["time_cost"] == pytest.approx(0.041666666666666664)

    def test_benchmark_isolation(self, db_session, sample_data):
        """Test that data from different benchmarks is not mixed."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Create another benchmark with same dataset
        benchmark2 = Benchmark(
            id=str(uuid.uuid4()),
            name="Test Benchmark 2",
            description="Test 2",
            dataset_id=benchmark.dataset_id,
            metric_suite=["accuracy"],
            value_formula="business_value * success_score",
            time_value_rate=100.0
        )
        db_session.add(benchmark2)
        db_session.commit()

        # Create runs for both benchmarks
        run1 = create_evaluation_run(db_session, agent, benchmark)
        run2 = create_evaluation_run(db_session, agent, benchmark2)

        # Add results to both runs
        for golden in goldens:
            create_evaluation_result(db_session, run1, golden, {"accuracy": 0.9})
            create_evaluation_result(db_session, run2, golden, {"accuracy": 0.5})

        # Get leaderboard for first benchmark only
        service = ComparisonService(db_session)
        leaderboard = service.get_benchmark_leaderboard(benchmark.id)

        # Should only include runs from benchmark 1
        assert len(leaderboard) == 1
        assert leaderboard[0]["avg_score"] == pytest.approx(0.9)

        # Get leaderboard for second benchmark
        leaderboard2 = service.get_benchmark_leaderboard(benchmark2.id)

        assert len(leaderboard2) == 1
        assert leaderboard2[0]["avg_score"] == pytest.approx(0.5)

    def test_leaderboard_sorting(self, db_session, sample_data):
        """Test that leaderboard sorting works correctly."""
        benchmark = sample_data["benchmark"]
        agent_a = sample_data["agent_a"]
        agent_b = sample_data["agent_b"]
        goldens = sample_data["goldens"]

        # Create runs
        run_a = create_evaluation_run(db_session, agent_a, benchmark)
        run_b = create_evaluation_run(db_session, agent_b, benchmark)

        # Add results with different costs (all successful)
        for golden in goldens:
            result_a = create_evaluation_result(db_session, run_a, golden, {"accuracy": 0.9})
            result_a.total_cost = "2.0"  # Higher cost
            db_session.commit()

            result_b = create_evaluation_result(db_session, run_b, golden, {"accuracy": 0.8})
            result_b.total_cost = "0.5"  # Lower cost
            db_session.commit()

        # Get leaderboard sorted by cost_per_success
        service = ComparisonService(db_session)
        leaderboard = service.get_benchmark_leaderboard(benchmark.id, sort_by="cost_per_success", sort_order="asc")

        # Agent B should be first (lower cost per success)
        # Agent A: 3 results * 2.0 = 6.0 total cost, 3 successes -> cost_per_success = 2.0
        # Agent B: 3 results * 0.5 = 1.5 total cost, 3 successes -> cost_per_success = 0.5
        assert len(leaderboard) == 2
        assert leaderboard[0]["agent_id"] == agent_b.id
        assert leaderboard[1]["agent_id"] == agent_a.id
        assert leaderboard[0]["cost_per_success"] == pytest.approx(0.5)
        assert leaderboard[1]["cost_per_success"] == pytest.approx(2.0)

    def test_missing_human_cost_handling(self, db_session, sample_data):
        """Test that missing human_cost data is handled gracefully."""
        benchmark = sample_data["benchmark"]
        agent = sample_data["agent_a"]
        goldens = sample_data["goldens"]

        # Remove human_cost from one golden
        goldens[0].human_cost = None
        db_session.commit()

        # Create a run
        run = create_evaluation_run(db_session, agent, benchmark)

        # All successful
        for golden in goldens:
            create_evaluation_result(db_session, run, golden, {"accuracy": 0.9})

        # Calculate stats
        service = ComparisonService(db_session)
        stats = service._calculate_agent_stats(agent.id, [run], benchmark.time_value_rate)

        # human_replacement should still be calculated using available data
        assert stats["human_replacement"] is not None
        # avg_human_cost = (50 + 50) / 2 = 50 (only 2 goldens have human_cost)
        # cost_per_success = 3.0 / 3 = 1.0
        # human_replacement = 1.0 / 50.0 = 0.02
        assert stats["human_replacement"] == pytest.approx(0.02)