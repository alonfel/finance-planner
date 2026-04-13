"""Profile-based data layer for multi-user support and future database migration.

This module manages the organization of all data files under data/profiles/{profile}/,
with automatic migration from the legacy flat file structure on first run.

Future enhancement: Replace all file I/O with database queries without changing this module's interface.
"""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


# Root data directory
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_PROFILE = "default"

# Read profile from environment variable, or use default
ACTIVE_PROFILE = os.environ.get("FINANCE_PROFILE", DEFAULT_PROFILE)


def get_profile_dir(profile: str = None) -> Path:
    """Get the root directory for a profile.

    Args:
        profile: Profile name (default: ACTIVE_PROFILE env var or "default")

    Returns:
        Path to data/profiles/{profile}/
    """
    if profile is None:
        profile = ACTIVE_PROFILE
    return DATA_DIR / "profiles" / profile


def get_settings_path(profile: str = None) -> Path:
    """Get the settings.json path for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "settings.json"


def get_scenarios_path(profile: str = None) -> Path:
    """Get the scenarios.json path for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "scenarios.json"


def get_scenario_nodes_path(profile: str = None) -> Path:
    """Get the scenario_nodes.json path for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "scenario_nodes.json"


def get_analysis_config_path(profile: str = None) -> Path:
    """Get the analysis config (config.json) path for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "analyses" / "config.json"


def get_cache_path(profile: str = None) -> Path:
    """Get the simulation cache path for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "analyses" / "cache" / "simulation_cache.json"


def get_results_dir(profile: str = None) -> Path:
    """Get the run results directory for a profile."""
    if profile is None:
        profile = ACTIVE_PROFILE
    return get_profile_dir(profile) / "analyses" / "results"


def profile_exists(profile: str = DEFAULT_PROFILE) -> bool:
    """Check if a profile exists (directory + profile.json both present).

    Args:
        profile: Profile name

    Returns:
        True if both the profile directory and profile.json exist
    """
    profile_dir = get_profile_dir(profile)
    profile_file = profile_dir / "profile.json"
    return profile_dir.exists() and profile_file.exists()


def _create_directory_structure(profile: str) -> None:
    """Create all necessary directories for a profile."""
    dirs = [
        get_profile_dir(profile),
        get_profile_dir(profile) / "analyses",
        get_profile_dir(profile) / "analyses" / "cache",
        get_results_dir(profile),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def create_profile(name: str, description: str = "", migrated_from: Optional[str] = None) -> None:
    """Create a new profile with metadata file.

    Idempotent: safe to call multiple times.

    Args:
        name: Profile name (e.g., "default", "john_doe")
        description: Human-readable description (optional)
        migrated_from: If set (e.g., "legacy"), adds migration metadata
    """
    profile = name
    _create_directory_structure(profile)

    profile_file = get_profile_dir(profile) / "profile.json"
    now_str = datetime.now().isoformat(timespec="seconds")

    # If profile.json already exists, don't overwrite
    if profile_file.exists():
        return

    profile_data = {
        "name": name,
        "description": description,
        "created_at": now_str,
    }

    if migrated_from:
        profile_data["migrated_from"] = migrated_from
        profile_data["migrated_at"] = now_str

    with open(profile_file, "w") as f:
        json.dump(profile_data, f, indent=2)


def _copy_file_if_exists(src: Path, dst: Path) -> bool:
    """Copy a file if source exists. Create parent directories as needed.

    Args:
        src: Source file path
        dst: Destination file path

    Returns:
        True if file was copied, False if source didn't exist
    """
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def migrate_to_data_layer(profile: str = DEFAULT_PROFILE) -> bool:
    """Auto-migrate legacy file structure to profile-based data layer.

    One-shot operation: if profile already exists, returns False (already migrated).

    Copies files from legacy locations:
        - <root>/settings.json → data/profiles/default/settings.json
        - <root>/scenarios.json → data/profiles/default/scenarios.json
        - scenario_analysis/scenario_nodes.json → data/profiles/default/scenario_nodes.json
        - scenario_analysis/analysis.json → data/profiles/default/analyses/config.json
        - scenario_analysis/simulation_cache.json → data/profiles/default/analyses/cache/simulation_cache.json

    Args:
        profile: Profile name (default: "default")

    Returns:
        True if migration was performed, False if profile already existed
    """
    if profile_exists(profile):
        # Already migrated
        return False

    # Create profile structure
    create_profile(profile, description="Auto-migrated from legacy structure", migrated_from="legacy")

    # Copy legacy files to new locations
    root = Path(__file__).parent.parent
    scenario_analysis = root / "scenario_analysis"

    files_to_copy = [
        (root / "settings.json", get_settings_path(profile)),
        (root / "scenarios.json", get_scenarios_path(profile)),
        (scenario_analysis / "scenario_nodes.json", get_scenario_nodes_path(profile)),
        (scenario_analysis / "analysis.json", get_analysis_config_path(profile)),
        (scenario_analysis / "simulation_cache.json", get_cache_path(profile)),
    ]

    for src, dst in files_to_copy:
        _copy_file_if_exists(src, dst)

    return True


def save_run_result(profile: str = DEFAULT_PROFILE, metadata: Optional[Dict[str, Any]] = None) -> Path:
    """Save analysis run result with timestamp.

    Args:
        profile: Profile name
        metadata: Dict containing analyses_run, cache_generated_at, num_scenarios, etc.

    Returns:
        Path to the saved result file
    """
    results_dir = get_results_dir(profile)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped filename (e.g., 2026-04-12T09_15_22.json)
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%dT%H_%M_%S")
    result_file = results_dir / f"{timestamp}.json"

    result_data = {
        "run_at": now.isoformat(timespec="seconds"),
        "profile": profile,
    }

    if metadata:
        result_data.update(metadata)

    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)

    return result_file
