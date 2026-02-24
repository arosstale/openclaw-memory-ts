#!/bin/bash
# Pi-Agent Automated Corrective Actions
# Automatically executes corrections when health check detects issues

set -euo pipefail

# ========================================
# Configuration
# ========================================
WORKSPACE="${WORKSPACE:-/home/majinbu/pi-mono-workspace}"
LOG_FILE="$WORKSPACE/logs/corrective-actions_$(date +%Y%m%d).log"
HEALTH_CHECK="$WORKSPACE/scripts/health-check.sh"
AUTO_CORRECT="${AUTO_CORRECT:-true}"  # Set to false to disable auto-correction

mkdir -p "$(dirname "$LOG_FILE")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ========================================
# Logging
# ========================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

# ========================================
# Corrective Actions
# ========================================

# ------------------------------------------------
# 1. Aggressive Git Pruning
# ------------------------------------------------
corrective_git_prune() {
    log_info "Running aggressive Git pruning..."
    
    cd "$WORKSPACE"
    
    # Check git folder size before
    local git_size_before=$(du -sh .git 2>/dev/null | cut -f1 || echo "N/A")
    log_info "Git size before: $git_size_before"
    
    # Aggressive garbage collection
    git gc --aggressive --prune=now 2>&1 | tee -a "$LOG_FILE" || true
    git prune-packed 2>&1 | tee -a "$LOG_FILE" || true
    git pack-refs --all 2>&1 | tee -a "$LOG_FILE" || true
    
    # Check git folder size after
    local git_size_after=$(du -sh .git 2>/dev/null | cut -f1 || echo "N/A")
    log_info "Git size after: $git_size_after"
    
    log_success "Git pruning complete: $git_size_before → $git_size_after"
}

# ------------------------------------------------
# 2. Archive Old Memories
# ------------------------------------------------
corrective_archive_memories() {
    log_info "Archiving memories older than 30 days..."
    
    local memory_dir="$WORKSPACE/memory"
    local archive_dir="$WORKSPACE/memory/archive"
    local archived_count=0
    
    mkdir -p "$archive_dir"
    
    # Find memory files older than 30 days
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            local archive_path="$archive_dir/$filename"
            
            # Move to archive
            mv "$file" "$archive_path" 2>/dev/null && {
                archived_count=$((archived_count + 1))
                log_info "Archived: $filename"
            }
        fi
    done < <(find "$memory_dir" -name "*.md" -type f -mtime +30 2>/dev/null | grep -v "archive/")
    
    log_success "Archived $archived_count memory files older than 30 days"
}

# ------------------------------------------------
# 3. Vacuum SQLite Databases
# ------------------------------------------------
corrective_vacuum_databases() {
    log_info "Vacuuming SQLite databases..."
    
    local vacuumed_count=0
    
    # Find all .db files
    while IFS= read -r dbfile; do
        if [ -f "$dbfile" ]; then
            log_info "Vacuuming: $dbfile"
            sqlite3 "$dbfile" "VACUUM;" 2>&1 | tee -a "$LOG_FILE" || true
            sqlite3 "$dbfile" "PRAGMA optimize;" 2>&1 | tee -a "$LOG_FILE" || true
            vacuumed_count=$((vacuumed_count + 1))
        fi
    done < <(find "$WORKSPACE" -name "*.db" -type f 2>/dev/null)
    
    log_success "Vacuumed $vacuumed_count SQLite databases"
}

# ------------------------------------------------
# 4. Clean Old Logs
# ------------------------------------------------
corrective_clean_logs() {
    log_info "Cleaning logs older than 7 days..."
    
    local cleaned_count=0
    
    # Find and remove old log files
    while IFS= read -r logfile; do
        if [ -f "$logfile" ]; then
            log_info "Cleaning: $logfile"
            rm "$logfile" 2>/dev/null && {
                cleaned_count=$((cleaned_count + 1))
            }
        fi
    done < <(find "$WORKSPACE/logs" -name "*.log" -type f -mtime +7 2>/dev/null)
    
    # Also clean .openclaw/logs
    while IFS= read -r logfile; do
        if [ -f "$logfile" ]; then
            rm "$logfile" 2>/dev/null && {
                cleaned_count=$((cleaned_count + 1))
            }
        fi
    done < <(find "$WORKSPACE/.openclaw/logs" -name "*.log" -type f -mtime +7 2>/dev/null)
    
    log_success "Cleaned $cleaned_count log files older than 7 days"
}

# ------------------------------------------------
# 5. Docker Cleanup
# ------------------------------------------------
corrective_docker_cleanup() {
    log_info "Running Docker cleanup..."
    
    if command -v docker &> /dev/null; then
        # Remove stopped containers
        local removed_containers=$(docker container prune -f 2>/dev/null | grep "Containers" | cut -d: -f2 | tr -d ' ' || echo "0")
        
        # Remove dangling images
        local removed_images=$(docker image prune -f 2>/dev/null | grep "Dangling" | cut -d: -f2 | tr -d ' ' || echo "0")
        
        # Remove unused volumes
        local removed_volumes=$(docker volume prune -f 2>/dev/null | grep "Volumes" | cut -d: -f2 | tr -d ' ' || echo "0")
        
        log_success "Docker cleanup: $removed_containers containers, $removed_images images, $removed_volumes volumes"
    else
        log_warn "Docker not available, skipping cleanup"
    fi
}

# ------------------------------------------------
# 6. Memory Template Consolidation
# ------------------------------------------------
corrective_consolidate_templates() {
    log_info "Consolidating memory templates..."
    
    local template_dir="$WORKSPACE/memory/templates"
    local consolidated_dir="$WORKSPACE/memory/templates/consolidated"
    
    if [ ! -d "$template_dir" ]; then
        log_info "No template directory found, skipping"
        return
    fi
    
    mkdir -p "$consolidated_dir"
    
    # Count templates
    local template_count=$(find "$template_dir" -name "*.md" -type f | grep -v consolidated | wc -l)
    
    if [ "$template_count" -gt 20 ]; then
        log_warn "Found $template_count templates (threshold: 20)"
        
        # Move older templates to consolidated
        local consolidated_count=0
        while IFS= read -r file; do
            local filename=$(basename "$file")
            mv "$file" "$consolidated_dir/$filename" 2>/dev/null && {
                consolidated_count=$((consolidated_count + 1))
            }
        done < <(find "$template_dir" -name "*.md" -type f -mtime +14 | grep -v consolidated)
        
        log_success "Consolidated $consolidated_count templates older than 14 days"
    else
        log_info "Template count ($template_count) is within threshold, no action needed"
    fi
}

# ------------------------------------------------
# 7. Remove Duplicate Memory Files
# ------------------------------------------------
corrective_remove_duplicates() {
    log_info "Checking for duplicate memory files..."
    
    local duplicate_count=0
    local seen_md5=""
    
    # Check for duplicates by content hash
    for file in "$WORKSPACE/memory"/*.md; do
        if [ -f "$file" ]; then
            local md5=$(md5sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "")
            
            if [ -n "$md5" ]; then
                if [[ "$seen_md5" == *"$md5"* ]]; then
                    log_warn "Duplicate found: $(basename "$file")"
                    # Move to duplicates folder
                    mkdir -p "$WORKSPACE/memory/duplicates"
                    mv "$file" "$WORKSPACE/memory/duplicates/" 2>/dev/null && {
                        duplicate_count=$((duplicate_count + 1))
                    }
                else
                    seen_md5="$seen_md5 $md5"
                fi
            fi
        fi
    done
    
    if [ "$duplicate_count" -gt 0 ]; then
        log_success "Removed $duplicate_count duplicate files"
    else
        log_info "No duplicates found"
    fi
}

# ------------------------------------------------
# 8. Compact Python Bytecode
# ------------------------------------------------
corrective_compact_bytecode() {
    log_info "Compiling Python bytecode for faster startup..."
    
    local compiled_count=0
    
    # Find all Python files
    while IFS= read -r pyfile; do
        if [ -f "$pyfile" ]; then
            python3 -m py_compile "$pyfile" 2>/dev/null && {
                compiled_count=$((compiled_count + 1))
            } || true
        fi
    done < <(find "$WORKSPACE" -name "*.py" -type f 2>/dev/null)
    
    log_success "Compiled $compiled_count Python files"
}

# ------------------------------------------------
# 9. Reset ALMA Design Cache
# ------------------------------------------------
corrective_reset_alma_cache() {
    log_info "Checking ALMA design cache..."
    
    local alma_db="$WORKSPACE/monitoring/alma_designs.db"
    
    if [ -f "$alma_db" ]; then
        # Count designs
        local design_count=$(sqlite3 "$alma_db" "SELECT COUNT(*) FROM designs;" 2>/dev/null || echo "0")
        
        if [ "$design_count" -gt 100 ]; then
            log_warn "ALMA cache has $design_count designs (threshold: 100)"
            
            # Archive old designs (keep only top 50 by score)
            sqlite3 "$alma_db" <<EOF 2>/dev/null
DELETE FROM designs
WHERE id NOT IN (
    SELECT id FROM designs
    ORDER BY score DESC, created_at DESC
    LIMIT 50
);
EOF
            
            log_success "Archived old ALMA designs, keeping top 50"
        else
            log_info "ALMA cache size is within threshold"
        fi
    else
        log_info "No ALMA database found"
    fi
}

# ========================================
# Auto-Correction Logic
# ========================================

run_health_check() {
    log_info "Running health check..."
    
    if [ -f "$HEALTH_CHECK" ]; then
        "$HEALTH_CHECK" 2>&1 | tee -a "$LOG_FILE"
        return ${PIPESTATUS[0]}
    else
        log_error "Health check script not found: $HEALTH_CHECK"
        return 1
    fi
}

analyze_and_correct() {
    log_info "Analyzing health check results and applying corrections..."
    
    # Read the latest health log
    local latest_log=$(ls -t "$WORKSPACE/health/health_check_"*.log 2>/dev/null | head -1)
    
    if [ -z "$latest_log" ]; then
        log_warn "No health log found, running fresh check"
        run_health_check
        latest_log=$(ls -t "$WORKSPACE/health/health_check_"*.log 2>/dev/null | head -1)
    fi
    
    if [ -z "$latest_log" ]; then
        log_error "Still no health log, cannot auto-correct"
        return 1
    fi
    
    # Analyze and apply corrections
    local corrections_applied=0
    
    # Check for Git bloat
    if grep -q "HIGH RISK: Git folder is bloated" "$latest_log"; then
        log_warn "Detected: Git bloat"
        if [ "$AUTO_CORRECT" = "true" ]; then
            corrective_git_prune
            corrections_applied=$((corrections_applied + 1))
        else
            log_warn "AUTO_CORRECT disabled, skipping git prune"
        fi
    fi
    
    # Check for old memories
    if grep -q "Archive memories older than 30 days" "$latest_log"; then
        log_warn "Detected: Old memories"
        if [ "$AUTO_CORRECT" = "true" ]; then
            corrective_archive_memories
            corrections_applied=$((corrections_applied + 1))
        else
            log_warn "AUTO_CORRECT disabled, skipping memory archive"
        fi
    fi
    
    # Check for large databases
    if grep -q "Vacuum large SQLite databases" "$latest_log"; then
        log_warn "Detected: Large SQLite databases"
        if [ "$AUTO_CORRECT" = "true" ]; then
            corrective_vacuum_databases
            corrections_applied=$((corrections_applied + 1))
        else
            log_warn "AUTO_CORRECT disabled, skipping database vacuum"
        fi
    fi
    
    # Check for HEAVIER verdict
    if grep -q "Verdict: Getting HEAVIER" "$latest_log"; then
        log_warn "Detected: System getting heavier"
        if [ "$AUTO_CORRECT" = "true" ]; then
            corrective_git_prune
            corrective_archive_memories
            corrective_vacuum_databases
            corrective_clean_logs
            corrective_consolidate_templates
            corrections_applied=$((corrections_applied + 5))
        else
            log_warn "AUTO_CORRECT disabled, skipping heavy corrections"
        fi
    fi
    
    # Always run these light corrections
    corrective_clean_logs
    
    if [ "$corrections_applied" -gt 0 ]; then
        log_success "Applied $corrections_applied corrective actions"
        
        # Re-run health check to verify
        log_info "Re-running health check to verify corrections..."
        run_health_check
    else
        log_info "No corrections needed"
    fi
    
    return 0
}

# ========================================
# Main
# ========================================

main() {
    echo "========================================"
    echo "Pi-Agent Automated Corrective Actions"
    echo "========================================"
    echo ""
    
    log_info "Starting corrective actions (AUTO_CORRECT=$AUTO_CORRECT)"
    
    if [ "$AUTO_CORRECT" = "true" ]; then
        log_info "Auto-correction: ENABLED"
    else
        log_warn "Auto-correction: DISABLED (run with AUTO_CORRECT=true to enable)"
    fi
    
    echo ""
    
    # Run analysis and corrections
    analyze_and_correct
    
    echo ""
    echo "========================================"
    echo "Corrective Actions Complete"
    echo "========================================"
    echo "Log saved to: $LOG_FILE"
}

# Run main
main "$@"
