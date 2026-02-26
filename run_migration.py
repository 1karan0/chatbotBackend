#!/usr/bin/env python3
"""
Script to migrate tenant_id from UUID to VARCHAR (String)
"""
import os

# Import required packages
try:
    from sqlalchemy import create_engine, text

    # Get database URL - hardcoded for now
    db_url = "postgresql://charbot_user:5E4TfARMyCzcSqsOEqckkbYCRG2kMVED@dpg-d3ads5gdl3ps73enmr5g-a.singapore-postgres.render.com/charbot"

    if not db_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        exit(1)

    print(f"Connecting to database...")
    engine = create_engine(db_url)

    # Execute the migration
    with engine.begin() as connection:
        # Check current type
        result = connection.execute(text(
            """SELECT data_type FROM information_schema.columns
            WHERE table_name='tenants' AND column_name='tenant_id'"""
        ))
        current_type = result.scalar()

        print(f"Current tenant_id type: {current_type}")

        if current_type == 'uuid':
            print('\n=== Applying migration to change tenant_id from UUID to VARCHAR ===\n')

            # 1. tenants table
            print('1. Converting tenants.tenant_id to VARCHAR...')
            connection.execute(text(
                'ALTER TABLE tenants ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text'
            ))
            print('   ✓ Done')

            # 2. backendusers table
            print('2. Converting backendusers.tenant_id to VARCHAR...')
            connection.execute(text(
                'ALTER TABLE backendusers DROP CONSTRAINT IF EXISTS backendusers_tenant_id_fkey'
            ))
            connection.execute(text(
                'ALTER TABLE backendusers ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text'
            ))
            connection.execute(text(
                'ALTER TABLE backendusers ADD CONSTRAINT backendusers_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE'
            ))
            print('   ✓ Done')

            # 3. knowledge_sources table
            print('3. Converting knowledge_sources.tenant_id to VARCHAR...')
            connection.execute(text(
                'ALTER TABLE knowledge_sources DROP CONSTRAINT IF EXISTS knowledge_sources_tenant_id_fkey'
            ))
            connection.execute(text(
                'ALTER TABLE knowledge_sources ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text'
            ))
            connection.execute(text(
                'ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE'
            ))
            print('   ✓ Done')

            print('\n=== Migration completed successfully! ===')
            print('\nAll tenant_id columns are now VARCHAR type.')

        elif current_type in ['character varying', 'varchar', 'text']:
            print('\n✓ tenant_id is already a string type. No migration needed.')
        else:
            print(f'\nUnexpected type: {current_type}')

except ImportError as e:
    print(f"ERROR: Missing required package - {e}")
    print("Please install required packages: pip install sqlalchemy psycopg2-binary python-dotenv")
    exit(1)
except Exception as e:
    print(f"ERROR: Migration failed - {e}")
    import traceback
    traceback.print_exc()
    exit(1)
