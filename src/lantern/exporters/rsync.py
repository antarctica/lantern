import logging
from collections.abc import Collection
from pathlib import Path
from tempfile import TemporaryDirectory

import sysrsync

from lantern.exporters.base import ExporterBase
from lantern.exporters.local import LocalExporter
from lantern.models.site import SiteContent


class RsyncExporter(ExporterBase):
    """
    Rsync exporter.

    For use with local and remote file systems.

    Wrapper around https://github.com/gchamon/sysrsync client, which requires the `rsync` binary to be installed.
    """

    def __init__(self, logger: logging.Logger, path: Path, host: str | None = None) -> None:
        """Initialise."""
        super().__init__(logger=logger)
        self._path = path
        self._host = host

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Rsync"

    def _upload_dir(self, src_path: Path, target_path: Path, target_host: str | None = None) -> None:
        """
        Copy contents of source path to target on local or remote server.

        The source and target path MUST be directories.

        E.g. for a source path './items' containing './items/123/index.html' and a target path of '/data/', this will
        create '/data/123/index.html'.

        Rsync options:
        - `-rlD`      : recurse, symlinks, devices/specials
        - `--no-perms`: don't chmod — new files/dirs inherit default ACLs automatically
        - `--no-times : don't set timestamps (as this requires ownership of the parent directory)

        Note: `-a` not used as it implies: `-p` (perms), `-o` (owner), `-g` (group), `-t` (times) — all of which can
        fail for non-owners.

        Explanation:
        > These options are necessary because rsync `-a/-p` for example tries to call chmod() on the target to match
        > source permissions. Even if the target directory has group-write, only the directory owner can chmod() it —
        > this is a Linux kernel restriction, not a permission bit issue. I.e. if the target was created by `alice`,
        > `bob` cannot change their permissions even with group-write access.
        """
        if not target_host and not target_path.exists():
            self._logger.info("Ensuring target local path exists.")
            target_path.mkdir(parents=True, exist_ok=True)

        target = f"{target_host}:{target_path}" if target_host else str(target_path)
        kwargs = {
            "source": str(src_path.resolve()),
            "sync_source_contents": True,
            "destination": str(target_path),
            "options": ["-rlD", "--no-perms", "--no-times"],  # to work around POSIX group-write limitations
        }
        if target_host:
            kwargs["destination_ssh"] = target_host

        self._logger.info(f"Syncing '{src_path.resolve()}' to '{target}'")
        sysrsync.run(strict=True, **kwargs)

    def export(self, content: Collection[SiteContent]) -> None:
        """
        Persist content.

        Requires materialised files to sync, created by dumping to a temp directory.
        """
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "output"
            tmp_exporter = LocalExporter(logger=self._logger, path=tmp_path)
            tmp_exporter.export(content)

            # `src_path=tmp_path` not used to allow ExporterLocal to be mocked in tests to give a predictable path.
            self._upload_dir(src_path=tmp_exporter.base_path, target_path=self._path, target_host=self._host)
            target = f"{self._host}:{self._path}" if self._host else str(self._path)
            self._logger.info(f"Exported {len(content)} items to '{target}'")
