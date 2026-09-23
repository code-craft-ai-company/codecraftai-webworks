"""
    Property test for asset integrity in the AssetResolver.

    This module verifies Property 2: Asset Integrity.

    For all entries in manifest.json, the SHA-256 checksum recorded SHALL
    match the actual file content.

    **Validates: Requirements 7.5, 7.6**
"""

import hashlib
import json
import os

from ccai.webworks.openapi.assets import AssetResolver


# =============================================================================
# Property Test
# =============================================================================

def test_property_asset_integrity():
    """
        **Validates: Requirements 7.5, 7.6**

        Property 2: Asset Integrity

        For all entries in manifest.json, verify the SHA-256 checksum
        matches the actual file content.  This test reads the manifest,
        iterates every recorded file, computes the SHA-256 digest of the
        on-disk file, and compares it to the expected value.
    """
    resolver = AssetResolver()

    # Load the manifest directly to iterate all entries
    # Use the resolver's own static dir
    static_dir = resolver._static_dir

    manifest_path = os.path.join(static_dir, "manifest.json")

    with open(manifest_path, "r", encoding="utf-8") as mf:
        manifest = json.load(mf)

    total_checks = 0

    for group_name, group_data in manifest.items():
        version = group_data.get("version")
        files_dict = group_data.get("files", {})

        # -----------------------------------------------------------------
        # Check 1: Each group with files should have a version
        # -----------------------------------------------------------------
        if len(files_dict) > 0 and version is None:
            errmsg = (
                "Asset group '{}' has files but no version recorded"
            ).format(group_name)
            raise AssertionError(errmsg)

        total_checks += 1

        for fname, file_info in files_dict.items():
            expected_sha = file_info.get("sha256")
            download_url = file_info.get("url")

            # ---------------------------------------------------------
            # Check 2: Each file entry should have a sha256 checksum
            # ---------------------------------------------------------
            if expected_sha is None:
                errmsg = (
                    "File '{}/{}' has no sha256 checksum in manifest"
                ).format(group_name, fname)
                raise AssertionError(errmsg)

            total_checks += 1

            # ---------------------------------------------------------
            # Check 3: Each file entry should have a download URL
            # ---------------------------------------------------------
            if download_url is None:
                errmsg = (
                    "File '{}/{}' has no download URL in manifest"
                ).format(group_name, fname)
                raise AssertionError(errmsg)

            total_checks += 1

            # ---------------------------------------------------------
            # Check 4: The file should exist on disk
            # ---------------------------------------------------------
            file_path = os.path.join(static_dir, group_name, fname)

            if not os.path.isfile(file_path):
                errmsg = (
                    "File '{}/{}' is listed in manifest but not found on disk"
                ).format(group_name, fname)
                raise AssertionError(errmsg)

            total_checks += 1

            # ---------------------------------------------------------
            # Check 5: SHA-256 checksum matches actual file content
            # ---------------------------------------------------------
            sha256_hash = hashlib.sha256()

            with open(file_path, "rb") as af:
                for chunk in iter(lambda: af.read(8192), b""):
                    sha256_hash.update(chunk)

            actual_sha = sha256_hash.hexdigest()

            if actual_sha != expected_sha:
                errmsg = (
                    "Checksum mismatch for '{}/{}': "
                    "expected='{}', actual='{}'"
                ).format(group_name, fname, expected_sha, actual_sha)
                raise AssertionError(errmsg)

            total_checks += 1

    # -----------------------------------------------------------------
    # Check 6: Verify the resolver's verify_integrity agrees
    # -----------------------------------------------------------------
    integrity_errors = resolver.verify_integrity()

    if len(integrity_errors) > 0:
        errmsg = (
            "AssetResolver.verify_integrity() reported errors: {}"
        ).format("; ".join(integrity_errors))
        raise AssertionError(errmsg)

    total_checks += 1

    # Verify we tested a meaningful number of entries
    if total_checks < 10:
        errmsg = "Expected at least 10 checks, got {}".format(total_checks)
        raise AssertionError(errmsg)

    return
