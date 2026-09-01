import logging
import time
from typing import TYPE_CHECKING

from lantern.exporters.base import ExporterBase

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

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
        super().__init__(logger=logger, name="Local Filesystem")
        self.base_path = path
        self._mode_dir = mode_d
        self._mode_file = mode_f

    def export(self, content: Collection[SiteContent]) -> None:
        """Persist content."""
        start = time.monotonic()
        count = 0
        prepared_dirs: set[Path] = set()

        for item in content:
            path = self.base_path / item.path

            # create parent directories and set permissions (using chmod to avoid umask)
            # directories are tracked so each is only prepared once, as many items share the same parents
            if path.parent not in prepared_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
                current = path.parent
                while current != self.base_path and current not in prepared_dirs:
                    current.chmod(self._mode_dir)
                    prepared_dirs.add(current)
                    current = current.parent

            item_content = item.content.encode("utf-8") if isinstance(item.content, str) else item.content
            with path.open(mode="wb") as f:
                f.write(item_content)
            path.chmod(mode=self._mode_file)

            # log any object metadata that local system doesn't support
            if self._logger.isEnabledFor(logging.DEBUG) and (item.object_meta or item.redirect):
                unsupported = {**item.object_meta}
                if item.redirect:
                    unsupported["redirect"] = item.redirect
                self._logger.debug("Additional properties for %s:", path.resolve())
                self._logger.debug(unsupported)

            count += 1

        self._logger.info(
            "Exported %s items to '%s' in %s seconds", count, self.base_path.resolve(), round(time.monotonic() - start)
        )
