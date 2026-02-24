#!/usr/bin/env python3
"""
OpenClaw Memory Template - Backup and Restore
Automated backup and disaster recovery for OpenClaw memory
"""

import json
import os
import sys
import tarfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import hashlib
import subprocess


class BackupError(Exception):
    """Backup error"""
    pass


class RestoreError(Exception):
    """Restore error"""
    pass


class BackupManager:
    """Backup and restore manager for OpenClaw memory"""

    def __init__(self, workspace: Optional[str] = None):
        """Initialize backup manager

        Args:
            workspace: Path to OpenClaw workspace
        """
        if workspace:
            self.workspace = Path(workspace)
        else:
            self.workspace = Path(os.environ.get("OPENCLAW_WORKSPACE", "."))

        self.memory_dir = self.workspace / "memory"
        self.core_dir = self.workspace / ".openclaw" / "core"
        self.backup_dir = self.workspace / "backups"

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file

        Args:
            file_path: Path to file

        Returns:
            Hex checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_backup_name(self, prefix: str = "backup") -> str:
        """Generate backup filename with timestamp

        Args:
            prefix: Filename prefix

        Returns:
            Backup filename
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.tar.gz"

    def create_backup(
        self,
        backup_name: Optional[str] = None,
        compress: bool = True,
        checksum: bool = True
    ) -> dict:
        """Create backup of memory and core

        Args:
            backup_name: Custom backup name (default: auto-generated)
            compress: Whether to compress with gzip
            checksum: Whether to calculate checksums

        Returns:
            Backup metadata dict

        Raises:
            BackupError: If backup fails
        """
        if not backup_name:
            backup_name = self._get_backup_name()

        backup_path = self.backup_dir / backup_name

        print(f"📦 Creating backup: {backup_name}")
        print(f"   Memory dir: {self.memory_dir}")
        print(f"   Core dir: {self.core_dir}")
        print(f"   Output: {backup_path}")

        # Collect files to backup
        files_to_backup: List[Path] = []

        if self.memory_dir.exists():
            files_to_backup.extend(self.memory_dir.rglob("*"))

        if self.core_dir.exists():
            files_to_backup.extend(self.core_dir.rglob("*"))

        # Create backup
        mode = "w:gz" if compress else "w"
        with tarfile.open(backup_path, mode) as tar:
            for file_path in files_to_backup:
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.workspace)
                    tar.add(file_path, arcname=relative_path)
                    print(f"   Added: {relative_path}")

        # Calculate checksums
        checksums = {}
        if checksum:
            print("🔐 Calculating checksums...")
            for file_path in files_to_backup:
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.workspace))
                    checksums[relative_path] = self._calculate_checksum(file_path)

        # Create metadata
        metadata = {
            "name": backup_name,
            "path": str(backup_path),
            "created_at": datetime.utcnow().isoformat(),
            "files_count": len(files_to_backup),
            "compressed": compress,
            "checksums": checksums,
            "size_bytes": backup_path.stat().st_size
        }

        # Save metadata
        metadata_path = backup_path.with_suffix(".meta.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Backup complete!")
        print(f"   Files: {metadata['files_count']}")
        print(f"   Size: {metadata['size_bytes']} bytes")

        return metadata

    def list_backups(self) -> List[dict]:
        """List all available backups

        Returns:
            List of backup metadata dicts
        """
        backups = []

        for meta_file in self.backup_dir.glob("*.meta.json"):
            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
                    backups.append(metadata)
            except Exception as e:
                print(f"⚠️  Failed to read {meta_file}: {e}", file=sys.stderr)

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return backups

    def restore_backup(self, backup_name: str, verify_checksum: bool = True) -> dict:
        """Restore from backup

        Args:
            backup_name: Name of backup to restore
            verify_checksum: Whether to verify checksums

        Returns:
            Restore metadata dict

        Raises:
            RestoreError: If restore fails
        """
        backup_path = self.backup_dir / backup_name
        metadata_path = backup_path.with_suffix(".meta.json")

        if not backup_path.exists():
            raise RestoreError(f"Backup not found: {backup_name}")

        print(f"📦 Restoring backup: {backup_name}")

        # Load metadata
        with open(metadata_path) as f:
            metadata = json.load(f)

        print(f"   Created: {metadata['created_at']}")
        print(f"   Files: {metadata['files_count']}")

        # Verify checksums if available
        if verify_checksum and metadata.get("checksums"):
            print("🔐 Verifying checksums...")
            with tarfile.open(backup_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        try:
                            # Extract to temp location
                            temp_extract = self.workspace / ".openclaw" / "temp_restore"
                            temp_extract.mkdir(parents=True, exist_ok=True)

                            tar.extract(member, path=temp_extract)

                            extracted_path = temp_extract / member.name
                            if extracted_path.exists():
                                relative = f".openclaw/temp_restore/{member.name}"

                                # Calculate checksum
                                actual_checksum = self._calculate_checksum(extracted_path)
                                expected_checksum = metadata["checksums"].get(relative)

                                if expected_checksum and actual_checksum != expected_checksum:
                                    raise RestoreError(
                                        f"Checksum mismatch for {member.name}:\n"
                                        f"  Expected: {expected_checksum}\n"
                                        f"  Actual: {actual_checksum}"
                                    )

                                # Clean up temp
                                extracted_path.unlink()

                        except Exception as e:
                            print(f"⚠️  Checksum verification failed for {member.name}: {e}")

        # Extract backup
        print("📂 Extracting files...")
        mode = "r:gz" if metadata.get("compressed", True) else "r"
        with tarfile.open(backup_path, mode) as tar:
            tar.extractall(path=self.workspace)

        print("✅ Restore complete!")
        print(f"   Files extracted to: {self.workspace}")

        return {
            "name": backup_name,
            "restored_at": datetime.utcnow().isoformat(),
            "verified": verify_checksum
        }

    def prune_old_backups(self, keep_count: int = 10) -> int:
        """Remove old backups, keeping the most recent N

        Args:
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return 0

        # Backups to delete (oldest beyond keep_count)
        to_delete = backups[keep_count:]
        deleted_count = 0

        print(f"🧹 Pruning old backups (keeping {keep_count})...")

        for backup in to_delete:
            backup_path = self.backup_dir / backup["name"]
            metadata_path = backup_path.with_suffix(".meta.json")

            try:
                backup_path.unlink()
                metadata_path.unlink()
                print(f"   Deleted: {backup['name']}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Failed to delete {backup['name']}: {e}", file=sys.stderr)

        print(f"✅ Pruned {deleted_count} old backups")

        return deleted_count

    def auto_backup(self, interval_hours: int = 24) -> None:
        """Run auto backup (for cron)

        Args:
            interval_hours: Check if backup is recent (hours)
        """
        # Check last backup time
        backups = self.list_backups()

        if not backups:
            print("📦 No backups found, creating first backup...")
            self.create_backup()
            return

        last_backup = datetime.fromisoformat(backups[0]["created_at"])
        hours_since_backup = (datetime.utcnow() - last_backup).total_seconds() / 3600

        if hours_since_backup >= interval_hours:
            print(f"📦 Last backup was {hours_since_backup:.1f} hours ago, creating new backup...")
            self.create_backup()
            self.prune_old_backups(keep_count=10)
        else:
            print(f"✅ Recent backup found ({hours_since_backup:.1f} hours ago)")


# CLI interface
def main():
    """CLI for backup and restore"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenClaw Backup Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument("--name", help="Custom backup name")
    backup_parser.add_argument("--no-compress", action="store_true", help="Don't compress")
    backup_parser.add_argument("--no-checksum", action="store_true", help="Don't calculate checksums")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_name", help="Backup name to restore")
    restore_parser.add_argument("--no-verify", action="store_true", help="Don't verify checksums")

    # List command
    list_parser = subparsers.add_parser("list", help="List backups")

    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Remove old backups")
    prune_parser.add_argument("--keep", type=int, default=10, help="Number to keep (default: 10)")

    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Auto backup (for cron)")
    auto_parser.add_argument("--interval", type=int, default=24, help="Hours since last backup (default: 24)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get backup manager
    mgr = BackupManager()

    # Execute command
    if args.command == "backup":
        mgr.create_backup(
            backup_name=getattr(args, "name", None),
            compress=not getattr(args, "no_compress", False),
            checksum=not getattr(args, "no_checksum", False)
        )

    elif args.command == "restore":
        try:
            mgr.restore_backup(args.backup_name, verify_checksum=not getattr(args, "no_verify", False))
        except RestoreError as e:
            print(f"❌ Restore failed: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        backups = mgr.list_backups()
        if not backups:
            print("📦 No backups found")
        else:
            print(f"📦 Backups ({len(backups)}):")
            for backup in backups:
                print(f"  • {backup['name']}")
                print(f"    Created: {backup['created_at']}")
                print(f"    Size: {backup['size_bytes']} bytes")
                print()

    elif args.command == "prune":
        deleted = mgr.prune_old_backups(keep_count=args.keep)
        print(f"✅ Deleted {deleted} old backups")

    elif args.command == "auto":
        mgr.auto_backup(interval_hours=args.interval)


if __name__ == "__main__":
    main()
