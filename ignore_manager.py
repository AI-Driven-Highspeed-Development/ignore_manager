from __future__ import annotations

from pathlib import Path
from typing import Optional

from utils.logger_util import Logger


class IgnoreManager:
    """Programmatically manage .gitignore entries within a private zone.

    Manages entries ONLY within a marked "ADHD MANAGED" zone in .gitignore.
    Never touches anything outside the zone, even if duplicates exist.
    Creates the zone at the end of .gitignore if it doesn't exist.
    """

    ZONE_START = "# ========== ADHD MANAGED v1 - DO NOT EDIT =========="
    ZONE_END = "# ========== END ADHD MANAGED =========="

    def __init__(self, gitignore_path: Optional[str] = None) -> None:
        self.logger = Logger(name=__class__.__name__)

        if gitignore_path:
            self.gitignore_path = Path(gitignore_path)
        else:
            self.gitignore_path = self._find_project_root() / ".gitignore"

    # ---------------- Public API ----------------

    def ensure_ignored(self, path: str) -> bool:
        """Add path to .gitignore zone if not already present.

        Args:
            path: File or directory path/pattern to ignore (relative to repo root).

        Returns:
            True if entry was added, False if already present in zone.
        """
        pattern = self._normalize_pattern(path)

        if self.is_ignored(pattern):
            self.logger.debug(f"Already in zone: {pattern}")
            return False

        self._ensure_gitignore_exists()
        zone_entries = self._read_zone_entries()
        zone_entries.append(pattern)
        self._write_zone_entries(zone_entries)
        self.logger.info(f"Added to .gitignore zone: {pattern}")
        return True

    def is_ignored(self, path: str) -> bool:
        """Check if a path/pattern is in the managed zone.

        Args:
            path: File or directory path/pattern to check.

        Returns:
            True if the pattern exists in the managed zone.
        """
        pattern = self._normalize_pattern(path)
        entries = self._read_zone_entries()
        return pattern in entries

    def is_globally_ignored(self, path: str) -> bool:
        """Check if a path/pattern is anywhere in .gitignore (zone + outside).

        Args:
            path: File or directory path/pattern to check.

        Returns:
            True if the pattern exists anywhere in .gitignore.
        """
        pattern = self._normalize_pattern(path)
        all_entries = self._read_all_entries()
        return pattern in all_entries

    def add_ignore_pattern(self, pattern: str) -> bool:
        """Add a glob pattern to .gitignore zone.

        Args:
            pattern: Glob pattern (e.g., '*.log', 'build/', '**/*.pyc').

        Returns:
            True if pattern was added, False if already present.
        """
        return self.ensure_ignored(pattern)

    def remove_entry(self, path: str) -> bool:
        """Remove a path/pattern from the managed zone.

        Args:
            path: File or directory path/pattern to remove.

        Returns:
            True if entry was removed, False if not found in zone.
        """
        pattern = self._normalize_pattern(path)
        entries = self._read_zone_entries()

        if pattern not in entries:
            self.logger.debug(f"Not found in zone: {pattern}")
            return False

        entries.remove(pattern)
        self._write_zone_entries(entries)
        self.logger.info(f"Removed from .gitignore zone: {pattern}")
        return True

    def list_entries(self) -> list[str]:
        """List all entries in the managed zone.

        Returns:
            List of gitignore patterns in the zone.
        """
        return self._read_zone_entries()

    def ensure_multiple(self, paths: list[str]) -> dict[str, bool]:
        """Add multiple paths to .gitignore zone.

        Args:
            paths: List of file/directory paths/patterns to ignore.

        Returns:
            Dict mapping each path to whether it was added (True) or already present (False).
        """
        results = {}
        for path in paths:
            results[path] = self.ensure_ignored(path)
        return results

    # ---------------- Internal helpers ----------------

    def _find_project_root(self) -> Path:
        """Find the project root by looking for init.yaml or .git."""
        current = Path.cwd()

        for parent in [current] + list(current.parents):
            if (parent / "init.yaml").exists() or (parent / ".git").exists():
                return parent

        return current

    def _ensure_gitignore_exists(self) -> None:
        """Create .gitignore if it doesn't exist."""
        if not self.gitignore_path.exists():
            self.gitignore_path.touch()
            self.logger.info(f"Created .gitignore at {self.gitignore_path}")

    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize a pattern for consistent comparison."""
        return pattern.strip()

    def _read_lines(self) -> list[str]:
        """Read all lines from .gitignore."""
        if not self.gitignore_path.exists():
            return []
        content = self.gitignore_path.read_text(encoding="utf-8")
        return content.splitlines()

    def _find_zone(self, lines: list[str]) -> tuple[int, int] | None:
        """Find the start and end indices of the managed zone.

        Returns:
            Tuple of (start_index, end_index) or None if zone not found.
        """
        start = end = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("# ========== ADHD MANAGED"):
                start = i
            elif stripped.startswith("# ========== END ADHD MANAGED"):
                end = i
                break

        if start >= 0 and end > start:
            return (start, end)

        # Handle corrupted zone (only start or only end)
        if start >= 0 and end == -1:
            self.logger.warning("Corrupted zone: start marker without end. Will recreate.")
            return None
        if end >= 0 and start == -1:
            self.logger.warning("Corrupted zone: end marker without start. Will recreate.")
            return None

        return None

    def _read_zone_entries(self) -> list[str]:
        """Read entries from within the managed zone only."""
        lines = self._read_lines()
        zone = self._find_zone(lines)

        if zone is None:
            return []

        start, end = zone
        entries = []
        for line in lines[start + 1:end]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                entries.append(stripped)

        return entries

    def _read_all_entries(self) -> list[str]:
        """Read all non-comment, non-blank entries from entire .gitignore."""
        lines = self._read_lines()
        entries = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                entries.append(stripped)
        return entries

    def _write_zone_entries(self, entries: list[str]) -> None:
        """Write entries to the managed zone, preserving content outside."""
        self._ensure_gitignore_exists()
        lines = self._read_lines()
        zone = self._find_zone(lines)

        # Build the zone content
        zone_lines = [self.ZONE_START]
        for entry in entries:
            zone_lines.append(entry)
        zone_lines.append(self.ZONE_END)

        if zone is None:
            # No zone exists - append at end with blank line separator
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend(zone_lines)
        else:
            # Replace existing zone content
            start, end = zone
            lines = lines[:start] + zone_lines + lines[end + 1:]

        # Write back with proper newline at end
        content = "\n".join(lines)
        if content and not content.endswith("\n"):
            content += "\n"
        self.gitignore_path.write_text(content, encoding="utf-8")
