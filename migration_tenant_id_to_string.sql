-- =====================================================
-- Migration: Change tenant_id from UUID to VARCHAR
-- =====================================================
-- This migration converts tenant_id columns from UUID
-- to VARCHAR (string) across all tables
-- =====================================================

-- First, check current data types
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'tenant_id'
    AND table_name IN ('tenants', 'backendusers', 'knowledge_sources')
ORDER BY table_name;

-- =====================================================
-- Step 1: Convert tenants.tenant_id from UUID to VARCHAR
-- =====================================================
ALTER TABLE tenants
    ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;

-- =====================================================
-- Step 2: Convert backendusers.tenant_id from UUID to VARCHAR
-- =====================================================
-- Drop foreign key constraint first
ALTER TABLE backendusers
    DROP CONSTRAINT IF EXISTS backendusers_tenant_id_fkey;

-- Convert column type
ALTER TABLE backendusers
    ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;

-- Recreate foreign key constraint
ALTER TABLE backendusers
    ADD CONSTRAINT backendusers_tenant_id_fkey
    FOREIGN KEY (tenant_id)
    REFERENCES tenants(tenant_id)
    ON DELETE CASCADE;

-- =====================================================
-- Step 3: Convert knowledge_sources.tenant_id from UUID to VARCHAR
-- =====================================================
-- Drop foreign key constraint first
ALTER TABLE knowledge_sources
    DROP CONSTRAINT IF EXISTS knowledge_sources_tenant_id_fkey;

-- Convert column type
ALTER TABLE knowledge_sources
    ALTER COLUMN tenant_id TYPE VARCHAR USING tenant_id::text;

-- Recreate foreign key constraint
ALTER TABLE knowledge_sources
    ADD CONSTRAINT knowledge_sources_tenant_id_fkey
    FOREIGN KEY (tenant_id)
    REFERENCES tenants(tenant_id)
    ON DELETE CASCADE;

-- =====================================================
-- Verify the migration
-- =====================================================
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'tenant_id'
    AND table_name IN ('tenants', 'backendusers', 'knowledge_sources')
ORDER BY table_name;

-- Check sample data to ensure conversion was successful
SELECT tenant_id, tenant_name FROM tenants LIMIT 5;

SELECT user_id, username, tenant_id FROM backendusers LIMIT 5;

SELECT source_id, tenant_id, source_type FROM knowledge_sources LIMIT 5;
