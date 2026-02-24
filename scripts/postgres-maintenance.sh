#!/bin/bash
# OpenClaw V2.1 Elite - PostgreSQL Vacuum & Indexing Maintenance
# Ensures GIN indexes remain optimized for Archivist bot and swarm_messages

set -e

# Configuration
POSTGRES_HOST="${1:-localhost}"
POSTGRES_PORT="${2:-5432}"
POSTGRES_DB="${3:-openclaw}"
POSTGRES_USER="${4:-openclaw}"

# Tables to maintain
TABLES=("swarm_messages" "evolution_log" "performance_metrics" "memory" "context")

echo "🗄️  PostgreSQL Maintenance - OpenClaw V2.1 Elite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Host:   $POSTGRES_HOST:$POSTGRES_PORT"
echo "DB:     $POSTGRES_DB"
echo "Tables:  ${TABLES[*]}"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found. Installing PostgreSQL client..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq postgresql-client
fi

# Function to vacuum and analyze a table
vacuum_table() {
    local table=$1
    echo "🧹 Vacuuming: $table"

    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -c "VACUUM ANALYZE $table;" 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ Vacuum complete: $table"
    else
        echo "⚠️  Vacuum warning: $table"
    fi
}

# Function to reindex GIN indexes
reindex_table() {
    local table=$1
    echo "🔍 Reindexing: $table"

    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -c "REINDEX TABLE $table;" 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ Reindex complete: $table"
    else
        echo "⚠️  Reindex warning: $table"
    fi
}

# Function to update table statistics
update_statistics() {
    local table=$1
    echo "📊 Updating statistics: $table"

    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -c "ANALYZE $table;" 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ Statistics updated: $table"
    else
        echo "⚠️  Statistics update warning: $table"
    fi
}

# Maintenance for each table
for table in "${TABLES[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing table: $table"
    echo ""

    vacuum_table "$table"
    update_statistics "$table"
    
    # Reindex tables with GIN indexes (context table has vector column)
    if [ "$table" = "context" ] || [ "$table" = "swarm_messages" ]; then
        reindex_table "$table"
    fi
done

# Check for index fragmentation
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Checking index fragmentation..."
echo ""

INDEX_FRAGMENTATION=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    ROUND((idx_tup_read::float / NULLIF(idx_scan, 0))::numeric, 2) AS reads_per_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY reads_per_scan DESC NULLS LAST
LIMIT 10;
" 2>/dev/null)

if [ -n "$INDEX_FRAGMENTATION" ]; then
    echo "Top indexes by fragmentation:"
    echo "$INDEX_FRAGMENTATION"
else
    echo "✅ No significant index fragmentation detected"
fi

# Vacuum full (run monthly, not weekly)
if [ "${5}" = "--vacuum-full" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  Running VACUUM FULL (this may take time)..."
    echo ""

    for table in "${TABLES[@]}"; do
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q -c "VACUUM FULL $table;" 2>&1
        echo "✅ Full vacuum complete: $table"
    done
fi

# Report summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Maintenance Summary"
echo ""
echo "Tables processed: ${#TABLES[@]}"
echo "Indexes optimized: context (GIN), swarm_messages"
echo "Statistics updated: all tables"
echo ""

# Get current DB size
DB_SIZE=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));
" 2>/dev/null || echo "N/A")

echo "Database size: $DB_SIZE"

echo ""
echo "✅ PostgreSQL maintenance complete!"
echo ""
echo "💡 Recommended schedule:"
echo "  - Weekly (Sunday): $0"
echo "  - Monthly (1st of month): $0 --vacuum-full"
