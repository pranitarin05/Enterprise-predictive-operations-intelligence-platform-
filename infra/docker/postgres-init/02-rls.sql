-- Row-Level Security setup.
-- This file is kept in the repo for documentation/fresh-install purposes,
-- but since our Postgres container already exists, we apply it manually
-- via psql (see Step 9 below) rather than relying on container re-init.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_users ON users
  USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

-- Note: 'true' as the second argument to current_setting means
-- "don't error if unset, just return NULL" -- important for admin/
-- migration connections that don't set a tenant context.
