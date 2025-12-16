"""Simple DuckDB test - verify database works."""
import duckdb
from pathlib import Path

def test_duckdb():
    """Test DuckDB database creation and operations."""
    print("=" * 60)
    print("DuckDB Test")
    print("=" * 60)

    # Create data directory
    db_path = Path("data/payroll.duckdb")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n1. Database path: {db_path.absolute()}")
    print(f"   Exists before: {db_path.exists()}")

    # Connect and create tables
    print("\n2. Creating database and tables...")
    conn = duckdb.connect(str(db_path))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payroll_data (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR,
            period_year INTEGER,
            period_month INTEGER,
            matricule VARCHAR,
            nom VARCHAR,
            prenom VARCHAR,
            salaire_brut DOUBLE,
            salaire_net DOUBLE,
            statut_validation BOOLEAN DEFAULT FALSE,
            edge_case_flag BOOLEAN DEFAULT FALSE,
            edge_case_reason VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id VARCHAR PRIMARY KEY,
            nom_societe VARCHAR,
            siret VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("   ✓ Tables created")

    # Show tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"\n3. Tables in database: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")

    # Test insert
    print("\n4. Testing insert...")
    conn.execute("""
        INSERT INTO companies (company_id, nom_societe, siret)
        VALUES ('TEST_COMPANY', 'Test Company SA', '12345678901234')
        ON CONFLICT DO NOTHING
    """)
    print("   ✓ Test company inserted")

    # Test query
    result = conn.execute("SELECT * FROM companies").fetchall()
    print(f"\n5. Companies in database: {len(result)}")
    for row in result:
        print(f"   - {row[0]}: {row[1]}")

    conn.close()

    print(f"\n6. Database file exists: {db_path.exists()}")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")

    print("\n" + "=" * 60)
    print("✓ DuckDB test successful!")
    print("=" * 60)

if __name__ == "__main__":
    test_duckdb()
