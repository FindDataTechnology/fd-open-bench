#!/usr/bin/env python3
"""Initialize database with default admin user."""

import sys
import os

# Set the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Change to project root to ensure .env is found
os.chdir(project_root)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import get_password_hash
from app.models import agent, dataset, golden, evaluation_run, evaluation_result, business_model, evaluator_config, trace

def init_db():
    """Initialize database tables and create default admin user."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Check if admin user already exists
    admin = db.query(User).filter(User.email == "admin@example.com").first()

    if admin:
        print("Admin user already exists")
    else:
        print("Creating default admin user...")
        admin = User(
            id="admin-001",
            email="admin@example.com",
            name="Admin User",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        print("\n" + "="*50)
        print("Default Login Credentials:")
        print("="*50)
        print("Email:    admin@example.com")
        print("Password: admin123")
        print("="*50 + "\n")

    db.close()

if __name__ == "__main__":
    init_db()
