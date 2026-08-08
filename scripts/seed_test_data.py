#!/usr/bin/env python3
"""
Seed test data into the database for e2e tests.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.agent import Agent
from app.models.dataset import Dataset
from app.models.golden import Golden
from app.core.security import get_password_hash

def seed_test_data():
    """Seed test data into the database."""
    print("Seeding test data...")

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Seed admin user
        admin = db.query(User).filter(User.email == 'admin@example.com').first()
        if not admin:
            admin = User(
                id='admin-001',
                email='admin@example.com',
                password_hash=get_password_hash('admin123'),
                name='Admin User',
                role='admin',
                is_active=True
            )
            db.add(admin)
            print("✓ Created admin user")

        # Seed regular user
        user = db.query(User).filter(User.email == 'user@example.com').first()
        if not user:
            user = User(
                id='user-001',
                email='user@example.com',
                password_hash=get_password_hash('user123'),
                name='Regular User',
                role='user',
                is_active=True
            )
            db.add(user)
            print("✓ Created regular user")

        # Seed test agent
        agent = db.query(Agent).filter(Agent.id == 'agent-001').first()
        if not agent:
            agent = Agent(
                id='agent-001',
                name='Test Agent',
                description='Test agent for e2e tests',
                adapter_type='openai',
                config={'model': 'gpt-4o', 'temperature': 0.7},
                pricing_config={'type': 'tokens', 'pricing': {'gpt-4o': {'input_per_1k': 0.0025, 'output_per_1k': 0.01}}}
            )
            db.add(agent)
            print("✓ Created test agent")

        # Seed test dataset
        dataset = db.query(Dataset).filter(Dataset.id == 'dataset-001').first()
        if not dataset:
            dataset = Dataset(
                id='dataset-001',
                name='Test Dataset',
                description='Test dataset for e2e tests'
            )
            db.add(dataset)
            print("✓ Created test dataset")

            # Seed test goldens
            golden1 = Golden(
                id='golden-001',
                dataset_id='dataset-001',
                input='Test input 1',
                expected_output='Test output 1',
                business_value=10.0
            )
            golden2 = Golden(
                id='golden-002',
                dataset_id='dataset-001',
                input='Test input 2',
                expected_output='Test output 2',
                business_value=20.0
            )
            db.add(golden1)
            db.add(golden2)
            print("✓ Created test goldens")

        db.commit()
        print("\n✅ Test data seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding test data: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    seed_test_data()
