#!/usr/bin/env python3
"""
Database Initialization Script
Sets up PostgreSQL database for Smart Login Guardian
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'slg_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'slg_password_dev_only'),
    'database': 'postgres'  # Connect to default database first
}

TARGET_DB = os.getenv('POSTGRES_DB', 'smart_login_guardian')

def create_database():
    """Create the database if it doesn't exist"""
    print(f"🔧 Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (TARGET_DB,)
    )

    if cursor.fetchone():
        print(f"✅ Database '{TARGET_DB}' already exists")
    else:
        print(f"🔨 Creating database '{TARGET_DB}'...")
        cursor.execute(f'CREATE DATABASE {TARGET_DB}')
        print(f"✅ Database '{TARGET_DB}' created successfully")

    cursor.close()
    conn.close()

def run_schema():
    """Run the schema file"""
    print(f"\n📋 Running database schema...")

    # Connect to target database
    db_config = DB_CONFIG.copy()
    db_config['database'] = TARGET_DB

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Read schema file
    schema_path = Path(__file__).parent / 'schemas' / '001_initial_schema.sql'

    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False

    print(f"📖 Reading schema from {schema_path}")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Execute schema
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Schema applied successfully")
        return True
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def create_initial_data():
    """Create initial seed data"""
    print(f"\n🌱 Creating initial seed data...")

    db_config = DB_CONFIG.copy()
    db_config['database'] = TARGET_DB

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Create default tenant
        cursor.execute("""
            INSERT INTO tenants (name, slug, status)
            VALUES ('Demo Organization', 'demo-org', 'active')
            ON CONFLICT DO NOTHING
            RETURNING tenant_id;
        """)

        result = cursor.fetchone()
        if result:
            tenant_id = result[0]
            print(f"✅ Created default tenant: {tenant_id}")
        else:
            # Get existing tenant
            cursor.execute("SELECT tenant_id FROM tenants WHERE slug = 'demo-org'")
            tenant_id = cursor.fetchone()[0]
            print(f"✅ Using existing tenant: {tenant_id}")

        # Create demo admin user (password: Demo@123)
        # Password hash for "Demo@123" using werkzeug
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash("Demo@123")

        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, status, email_verified)
            VALUES ('admin@demo.com', %s, 'Demo Admin', 'active', true)
            ON CONFLICT (email) DO NOTHING
            RETURNING user_id;
        """, (password_hash,))

        result = cursor.fetchone()
        if result:
            user_id = result[0]
            print(f"✅ Created demo user: admin@demo.com")

            # Add user to tenant as admin
            cursor.execute("""
                INSERT INTO tenant_memberships (tenant_id, user_id, role)
                VALUES (%s, %s, 'org_admin')
                ON CONFLICT DO NOTHING;
            """, (tenant_id, user_id))
            print(f"✅ Assigned admin role to user")
        else:
            print(f"✅ Demo user already exists")

        conn.commit()
        print("✅ Initial data created successfully")

        print("\n" + "="*60)
        print("📧 Demo Login Credentials:")
        print("   Email: admin@demo.com")
        print("   Password: Demo@123")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"❌ Error creating initial data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_setup():
    """Verify database setup"""
    print(f"\n🔍 Verifying database setup...")

    db_config = DB_CONFIG.copy()
    db_config['database'] = TARGET_DB

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    print(f"✅ Found {len(tables)} tables:")
    for table in tables[:10]:  # Show first 10
        print(f"   • {table[0]}")
    if len(tables) > 10:
        print(f"   ... and {len(tables) - 10} more")

    # Check tenant and user
    cursor.execute("SELECT COUNT(*) FROM tenants")
    tenant_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    print(f"\n✅ Data summary:")
    print(f"   • Tenants: {tenant_count}")
    print(f"   • Users: {user_count}")

    cursor.close()
    conn.close()

    return True

def main():
    """Main initialization process"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     SMART LOGIN GUARDIAN - DATABASE INITIALIZATION               ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Step 1: Create database
        create_database()

        # Step 2: Run schema
        if not run_schema():
            print("\n❌ Failed to apply schema. Exiting.")
            return False

        # Step 3: Create initial data
        if not create_initial_data():
            print("\n⚠️ Warning: Initial data creation failed")

        # Step 4: Verify setup
        if verify_setup():
            print("\n" + "="*60)
            print("✅ DATABASE SETUP COMPLETE!")
            print("="*60)
            print("\nYou can now:")
            print("1. Start the backend services")
            print("2. Login with admin@demo.com / Demo@123")
            print("3. Begin monitoring authentication events")
            print()
            return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection error: {e}")
        print("\n💡 Make sure PostgreSQL is running:")
        print("   • Docker: make dev")
        print("   • Or install PostgreSQL locally")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
