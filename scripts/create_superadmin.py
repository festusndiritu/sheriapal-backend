#!/usr/bin/env python
"""
Create a superadmin account for Sheriapal.

Usage:
    python scripts/create_superadmin.py --email admin@example.com --password secure_password

Or run interactively:
    python scripts/create_superadmin.py
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import engine, create_db_and_tables
from app.models import User, Role
from utils.crypto import hash_password
from sqlmodel import Session, select


def create_superadmin(email: str, password: str):
    """Create a superadmin user."""
    # Ensure database exists
    create_db_and_tables()

    with Session(engine) as session:
        # Check if superadmin already exists
        statement = select(User).where(User.email == email)
        existing = session.exec(statement).first()
        if existing:
            print(f"❌ Error: User with email '{email}' already exists")
            return False

        # Create superadmin
        superadmin = User(
            email=email,
            hashed_password=hash_password(password),
            role=Role.SUPERADMIN.value,
            is_approved=True
        )
        session.add(superadmin)
        session.commit()
        session.refresh(superadmin)

        print(f"✅ Superadmin created successfully!")
        print(f"   ID: {superadmin.id}")
        print(f"   Email: {superadmin.email}")
        print(f"   Role: {superadmin.role}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Create a superadmin account for Sheriapal"
    )
    parser.add_argument(
        "--email",
        help="Superadmin email address",
        required=False
    )
    parser.add_argument(
        "--password",
        help="Superadmin password",
        required=False
    )

    args = parser.parse_args()

    # Get email
    if args.email:
        email = args.email
    else:
        email = input("Enter superadmin email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            return False

    # Validate email
    if "@" not in email or "." not in email:
        print("❌ Invalid email format")
        return False

    # Get password
    if args.password:
        password = args.password
    else:
        import getpass
        password = getpass.getpass("Enter superadmin password: ")
        if not password:
            print("❌ Password cannot be empty")
            return False

        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            return False

    # Validate password
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return False

    return create_superadmin(email, password)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

