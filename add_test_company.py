#!/usr/bin/env python3
import duckdb
from pathlib import Path

# Connect to database
db_path = Path("data/payroll.duckdb")
conn = duckdb.connect(str(db_path))

# Add test company
conn.execute("""
    INSERT INTO companies (
        company_id,
        nom_societe,
        siret,
        adresse,
        email,
        point_contact,
        planning_jour_paie
    )
    VALUES (
        'TEST001',
        'Société Test Monaco',
        '12345678901234',
        '1 Avenue des Spélugues, 98000 Monaco',
        'contact@test-monaco.mc',
        'Jean Dupont',
        25
    )
    ON CONFLICT (company_id) DO NOTHING
""")

print("✓ Company added successfully!")
print("\nCompany details:")
print("  ID: TEST001")
print("  Name: Société Test Monaco")
print("  SIRET: 12345678901234")
print("  Contact: Jean Dupont")
print("  Payday: 25th of month")

# Show all companies
result = conn.execute("SELECT company_id, nom_societe FROM companies").fetchall()
print(f"\nTotal companies in DB: {len(result)}")
for row in result:
    print(f"  - {row[0]}: {row[1]}")

conn.close()
