#!/usr/bin/env python3
"""
Clean up test data from the database after e2e tests.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.agent import Agent
from app.models.dataset import Dataset
from app.models.golden import Golden
from app.models.evaluation_run import EvaluationRun
from app.models.evaluation_result import EvaluationResult

def cleanup_test_data():
    """Clean up test data from the database."""
    print("Cleaning up test data...")

    db = SessionLocal()

    try:
        # Delete test evaluation results
        results = db.query(EvaluationResult).filter(
            EvaluationResult.id.like('test-%')
        ).all()
        for result in results:
            db.delete(result)
        print(f"✓ Deleted {len(results)} test evaluation results")

        # Delete test evaluation runs
        runs = db.query(EvaluationRun).filter(
            EvaluationRun.id.like('test-%')
        ).all()
        for run in runs:
            db.delete(run)
        print(f"✓ Deleted {len(runs)} test evaluation runs")

        # Delete test goldens
        goldens = db.query(Golden).filter(
            Golden.id.like('test-%') | Golden.id.like('golden-%')
        ).all()
        for golden in goldens:
            db.delete(golden)
        print(f"✓ Deleted {len(goldens)} test goldens")

        # Delete test datasets
        datasets = db.query(Dataset).filter(
            Dataset.id.like('test-%') | Dataset.id.like('dataset-%')
        ).all()
        for dataset in datasets:
            db.delete(dataset)
        print(f"✓ Deleted {len(datasets)} test datasets")

        # Delete test agents
        agents = db.query(Agent).filter(
            Agent.id.like('test-%') | Agent.id.like('agent-%')
        ).all()
        for agent in agents:
            db.delete(agent)
        print(f"✓ Deleted {len(agents)} test agents")

        # Delete test users (but keep admin and regular user)
        users = db.query(User).filter(
            User.id.like('test-%') &
            ~User.email.in_(['admin@example.com', 'user@example.com'])
        ).all()
        for user in users:
            db.delete(user)
        print(f"✓ Deleted {len(users)} test users")

        db.commit()
        print("\n✅ Test data cleaned up successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error cleaning up test data: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    cleanup_test_data()
