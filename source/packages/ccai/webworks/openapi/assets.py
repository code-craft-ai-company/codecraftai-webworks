"""
.. module:: assets
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Asset resolver and serving helpers for bundled Swagger UI
        and ReDoc static files.

.. moduleauthor:: Code Craft AI LLC

This module provides the AssetResolver class that resolves and serves
bundled static assets for Swagger UI and ReDoc documentation interfaces.
All assets are read from the ``static/`` directory co-located with this
module so the documentation UI functions without external network access.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import hashlib
import json
import os

from typing import Any, Dict, List, Optional


class AssetResolver:
    """
        Resolves and serves bundled static assets for Swagger UI and ReDoc.

        Uses the ``static/`` directory co-located with this module as the
        asset root.  All file reads use ``__file__``-relative paths so the
        assets work from both source trees and installed wheels.
    """

    MIME_TYPES: Dict[str, str] = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".json": "application/json",
        ".map": "application/json",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
    }

    def __init__(self):
        self._static_dir = os.path.join(os.path.dirname(__file__), "static")
        self._manifest = self._load_manifest()
        return

    def _load_manifest(self) -> dict:
        """
            Load manifest.json from the static directory.

            :returns: The parsed manifest dictionary, or an empty dictionary
                if the manifest file does not exist or cannot be parsed.
        """
        manifest_path = os.path.join(self._static_dir, "manifest.json")

        if not os.path.isfile(manifest_path):
            rtnval = {}
            return rtnval

        with open(manifest_path, "r", encoding="utf-8") as mf:
            rtnval = json.load(mf)

        return rtnval

    def resolve(self, asset_group: str, filename: str) -> Optional[bytes]:
        """
            Read a bundled asset file.

            :param asset_group: The asset group name such as 'swagger-ui'
                or 'redoc'.
            :param filename: File name within the asset group directory.

            :returns: File contents as bytes, or None if not found.
        """
        file_path = os.path.join(self._static_dir, asset_group, filename)

        if not os.path.isfile(file_path):
            rtnval = None
            return rtnval

        with open(file_path, "rb") as af:
            rtnval = af.read()

        return rtnval

    def content_type(self, filename: str) -> str:
        """
            Determine the Content-Type for a filename based on its extension.

            :param filename: The asset filename.

            :returns: MIME type string.  Defaults to 'application/octet-stream'
                if the extension is not recognized.
        """
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower()

        rtnval = self.MIME_TYPES.get(ext_lower, "application/octet-stream")

        return rtnval

    def verify_integrity(self) -> List[str]:
        """
            Verify all vendored assets match their manifest checksums.

            Iterates every entry in the manifest and computes the SHA-256
            checksum of the corresponding file on disk.  Any mismatch or
            missing file is reported as an error string in the returned list.

            :returns: List of error messages.  An empty list means all
                assets passed verification.
        """
        errors: List[str] = []

        for group_name, group_data in self._manifest.items():
            files_dict = group_data.get("files", {})

            for fname, file_info in files_dict.items():
                expected_sha = file_info.get("sha256")

                if expected_sha is None:
                    continue

                file_path = os.path.join(self._static_dir, group_name, fname)

                if not os.path.isfile(file_path):
                    error_msg = "Missing file: {}/{}".format(group_name, fname)
                    errors.append(error_msg)
                    continue

                sha256_hash = hashlib.sha256()

                with open(file_path, "rb") as af:
                    for chunk in iter(lambda: af.read(8192), b""):
                        sha256_hash.update(chunk)

                actual_sha = sha256_hash.hexdigest()

                if actual_sha != expected_sha:
                    error_msg = (
                        "Checksum mismatch for {}/{}: "
                        "expected={}, actual={}"
                    ).format(group_name, fname, expected_sha, actual_sha)
                    errors.append(error_msg)

        return errors

    @property
    def swagger_ui_version(self) -> Optional[str]:
        """
            Return the vendored Swagger UI version from the manifest.

            :returns: The version string, or None if not recorded.
        """
        swagger_data = self._manifest.get("swagger-ui", {})
        rtnval = swagger_data.get("version")

        return rtnval

    @property
    def redoc_version(self) -> Optional[str]:
        """
            Return the vendored ReDoc version from the manifest.

            :returns: The version string, or None if not recorded.
        """
        redoc_data = self._manifest.get("redoc", {})
        rtnval = redoc_data.get("version")

        return rtnval


class AssetUpdater:
    """
        Downloads and vendors the latest Swagger UI and ReDoc releases
        from their official GitHub repositories.

        This class provides methods to download distribution files from
        GitHub releases, compute SHA-256 checksums, and update the
        manifest.json file that records asset versions and integrity
        information.

        Usage via CLI::

            webworks openapi update-assets
            webworks openapi update-assets --swagger-version 5.18.2
            webworks openapi update-assets --redoc-version 2.1.5
    """

    SWAGGER_UI_GITHUB: str = "swagger-api/swagger-ui"
    REDOC_GITHUB: str = "Redocly/redoc"

    SWAGGER_UI_FILES: List[str] = [
        "swagger-ui-bundle.js",
        "swagger-ui.css",
        "favicon-32x32.png",
    ]

    REDOC_FILES: List[str] = [
        "redoc.standalone.js",
    ]

    SWAGGER_UI_BASE_URL: str = (
        "https://unpkg.com/swagger-ui-dist@{version}/{filename}"
    )

    REDOC_BASE_URL: str = (
        "https://cdn.redoc.ly/redoc/v{version}/bundles/{filename}"
    )

    GITHUB_API_URL: str = "https://api.github.com/repos/{repo}/releases/latest"

    def __init__(self, static_dir: Optional[str] = None):
        """
            Initialize the AssetUpdater.

            :param static_dir: Path to the static asset directory. If None,
                defaults to the ``static/`` directory co-located with this module.
        """
        if static_dir is not None:
            self._static_dir = static_dir
        else:
            self._static_dir = os.path.join(os.path.dirname(__file__), "static")

        return

    def update_swagger_ui(self, version: Optional[str] = None) -> Dict[str, Any]:
        """
            Download Swagger UI distribution files from GitHub releases.

            Downloads all files listed in :attr:`SWAGGER_UI_FILES`, places
            them in the ``swagger-ui/`` subdirectory, and updates the
            manifest with version and checksum information.

            :param version: Specific version to download, or None for latest.

            :returns: A dictionary with ``version`` and ``files`` keys
                summarizing what was downloaded.
        """
        import requests

        if version is None:
            version = self._get_latest_release(self.SWAGGER_UI_GITHUB)

        dest_dir = os.path.join(self._static_dir, "swagger-ui")
        os.makedirs(dest_dir, exist_ok=True)

        files_info: Dict[str, Dict[str, str]] = {}

        for filename in self.SWAGGER_UI_FILES:
            url = self.SWAGGER_UI_BASE_URL.format(version=version, filename=filename)
            dest_path = os.path.join(dest_dir, filename)
            sha256 = self._download_file(url=url, dest=dest_path)
            files_info[filename] = {
                "url": url,
                "sha256": sha256,
            }

        self._update_manifest(group="swagger-ui", version=version, files=files_info)

        rtnval = {
            "version": version,
            "files": files_info,
        }

        return rtnval

    def update_redoc(self, version: Optional[str] = None) -> Dict[str, Any]:
        """
            Download ReDoc standalone bundle from GitHub releases.

            Downloads the ReDoc standalone JavaScript file, places it in
            the ``redoc/`` subdirectory, and updates the manifest with
            version and checksum information.

            :param version: Specific version to download, or None for latest.

            :returns: A dictionary with ``version`` and ``files`` keys
                summarizing what was downloaded.
        """
        import requests

        if version is None:
            version = self._get_latest_release(self.REDOC_GITHUB)

        dest_dir = os.path.join(self._static_dir, "redoc")
        os.makedirs(dest_dir, exist_ok=True)

        files_info: Dict[str, Dict[str, str]] = {}

        for filename in self.REDOC_FILES:
            url = self.REDOC_BASE_URL.format(version=version, filename=filename)
            dest_path = os.path.join(dest_dir, filename)
            sha256 = self._download_file(url=url, dest=dest_path)
            files_info[filename] = {
                "url": url,
                "sha256": sha256,
            }

        self._update_manifest(group="redoc", version=version, files=files_info)

        rtnval = {
            "version": version,
            "files": files_info,
        }

        return rtnval

    def _download_file(self, url: str, dest: str) -> str:
        """
            Download a file and return its SHA-256 checksum.

            :param url: URL to download from.
            :param dest: Local file path to write to.

            :returns: Hex-encoded SHA-256 checksum of the downloaded content.

            :raises: RuntimeError if the download fails.
        """
        import requests

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            errmsg = "Failed to download {}: HTTP {}".format(url, response.status_code)
            raise RuntimeError(errmsg)

        content = response.content

        sha256_hash = hashlib.sha256()
        sha256_hash.update(content)
        checksum = sha256_hash.hexdigest()

        with open(dest, "wb") as fh:
            fh.write(content)

        rtnval = checksum

        return rtnval

    def _update_manifest(self, group: str, version: str, files: Dict[str, Dict[str, str]]) -> None:
        """
            Update manifest.json with new version and checksum info.

            Reads the existing manifest (if present), updates the entry
            for the specified group, and writes the result back to disk.

            :param group: Asset group name such as 'swagger-ui' or 'redoc'.
            :param version: Version string for the downloaded release.
            :param files: Dictionary mapping filename to a dict with
                ``url`` and ``sha256`` keys.
        """
        manifest_path = os.path.join(self._static_dir, "manifest.json")

        manifest: Dict[str, Any] = {}

        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as mf:
                manifest = json.load(mf)

        manifest[group] = {
            "version": version,
            "files": files,
        }

        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, indent=4)
            mf.write("\n")

        return

    def _get_latest_release(self, repo: str) -> str:
        """
            Query GitHub API for the latest release tag.

            :param repo: GitHub repo in 'owner/name' format.

            :returns: Version tag string with the leading 'v' stripped
                if present.

            :raises: RuntimeError if the GitHub API request fails.
        """
        import requests

        api_url = self.GITHUB_API_URL.format(repo=repo)
        response = requests.get(api_url, timeout=30)

        if response.status_code != 200:
            errmsg = "Failed to query GitHub API for {}: HTTP {}".format(
                repo, response.status_code
            )
            raise RuntimeError(errmsg)

        data = response.json()
        tag_name = data.get("tag_name", "")

        if tag_name.startswith("v"):
            rtnval = tag_name[1:]
        else:
            rtnval = tag_name

        return rtnval
