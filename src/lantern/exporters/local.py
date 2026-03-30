import logging
from collections.abc import Collection
from pathlib import Path

from lantern.exporters.base import ExporterBase
from lantern.models.site import SiteContent


class LocalExporter(ExporterBase):
    """
    Local exporter.

    Dump outputs to a local file system.

    Optionally, file and directory modes can be configured. These are set prior to upload by rsync and preserved.

    Default directory mode: 0022 (rwx-r-x-r-x)
    Default file mode: 0222 (rw-r--r--)

    Intended for use with other exporters (such as `lantern.exporters.rsync.RsyncExporter`) or external processes.

    Note: `pathlib.Path.mkdir(mode=...)` is subject to the Python process umask, meaning the default directory mode
    typically resolves to 755 (rwxr-xr-x) rather than 777 (rwxrwxrwx). This is intentional.
    """

    def __init__(self, logger: logging.Logger, path: Path, mode_d: int = 0o755, mode_f: int = 0o644) -> None:
        """Initialise."""
        super().__init__(logger=logger)
        self.base_path = path
        self._mode_dir = mode_d
        self._mode_file = mode_f

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Local Filesystem"

    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        count = 0
        for item in content:
            path = self.base_path / item.path

            # create parent directories and set permissions (using chmod to avoid umask)
            path.parent.mkdir(parents=True, exist_ok=True)
            current = path.parent
            while current != self.base_path:
                current.chmod(self._mode_dir)
                current = current.parent

            item_content = item.content.encode("utf-8") if isinstance(item.content, str) else item.content
            with path.open(mode="wb") as f:
                f.write(item_content)
            path.chmod(mode=self._mode_file)

            # log any object metadata that local system doesn't support
            if self._logger.isEnabledFor(logging.DEBUG) and (item.object_meta or item.redirect):
                if item.redirect:
                    item.object_meta["redirect"] = item.redirect
                self._logger.debug(f"Additional properties for {path.resolve()}:")
                self._logger.debug(item.object_meta)

            count += 1

        self._logger.info(f"Exported {count} items to '{self.base_path.resolve()}'.")
