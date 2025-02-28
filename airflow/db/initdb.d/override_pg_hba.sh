#!/bin/bash
echo "🔧 Overriding pg_hba.conf..."
cp /docker-entrypoint-initdb.d/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf
chown postgres:postgres /var/lib/postgresql/data/pg_hba.conf
chmod 600 /var/lib/postgresql/data/pg_hba.conf

echo "🔄 Restarting PostgreSQL to apply changes..."
pg_ctl reload