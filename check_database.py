"""Verify DuckDB database setup."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from paie_reflex.services.data_mgt import DataManager

def check_database():
    """Check database setup and display info."""
    print("=" * 60)
    print("DuckDB Database Check")
    print("=" * 60)

    # Initialize database
    try:
        DataManager.init_database()
        print("✓ Database initialized")
        print(f"  Location: {DataManager.DB_PATH.absolute()}")
        print(f"  Exists: {DataManager.DB_PATH.exists()}")
        if DataManager.DB_PATH.exists():
            size_mb = DataManager.DB_PATH.stat().st_size / (1024 * 1024)
            print(f"  Size: {size_mb:.2f} MB")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

    # Check tables
    try:
        conn = DataManager.get_connection()

        # List tables
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"\n✓ Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  - {table_name}: {count} rows")

        conn.close()
    except Exception as e:
        print(f"✗ Table check failed: {e}")
        return False

    # Check companies
    try:
        companies = DataManager.get_companies()
        print(f"\n✓ Companies: {len(companies)}")
        for company in companies:
            print(f"  - {company}")
    except Exception as e:
        print(f"✗ Company check failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("Database check complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
