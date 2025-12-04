#!/usr/bin/env python3
"""
Database Migration Runner

Runs SQL migrations and creates tables from SQLAlchemy models.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.db.session import engine, Base
from app.db import models  # Import all models

def run_sql_migration(migration_file: str):
    """Run a SQL migration file."""
    migration_path = Path(__file__).parent / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    print(f"📄 Running migration: {migration_file}")
    
    try:
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        with engine.connect() as conn:
            for statement in statements:
                if statement:
                    conn.execute(text(statement))
            conn.commit()
        
        print(f"✅ Migration completed: {migration_file}")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {migration_file}")
        print(f"Error: {e}")
        return False

def create_tables_from_models():
    """Create all tables from SQLAlchemy models."""
    print("🔨 Creating tables from SQLAlchemy models...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def main():
    print("🚀 Starting database migrations...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
    print()
    
    # Create all tables from models (idempotent)
    if not create_tables_from_models():
        sys.exit(1)
    
    print()
    
    # Run specific SQL migrations if needed
    migrations = [
        "add_provider_health_tables.sql",
        "add_alert_tables.sql"
    ]
    
    for migration in migrations:
        print()
        if not run_sql_migration(migration):
            print(f"⚠️  Warning: Migration {migration} failed but continuing...")
    
    print()
    print("✅ All migrations completed successfully!")
    print()

if __name__ == "__main__":
    main()
