import csv
from functools import cached_property
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from lantern.models.checks import CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputSite

if TYPE_CHECKING:
    import logging


class RedirectsOutput(OutputSite):
    """
    Redirects output.

    Processes redirects defined in a set of content items. Generates a CSV file for use in other systems.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, content: list[SiteContent]) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Redirects", check_type=CheckType.NONE)
        self._items = content

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        meta = {"build_key": self._meta.build_key}
        if self._meta.build_repo_ref:
            meta["build_ref"] = self._meta.build_repo_ref
        return meta

    @property
    def _data(self) -> list[dict[str, str]]:
        """
        Assemble redirects data.

        The build commit (if known) and time are included to allow systems to check whether a redirects file is
        different to one previous processed (a more intelligent diff/check is recommended if updates are expensive).

        Where a content item points to an index.html file (e.g. `/foo/index.html`), additional redirects are added for
        `/foo/` or `/foo` (used for pretty URLs), as redirect matches are sensitive to the exact path.
        """
        build_commit = self._meta.build_repo_ref or ""
        build_time = self._meta.build_time.isoformat()

        redirects = [(str(c.path), c.redirect) for c in self._items if c and c.redirect]
        for r in redirects:
            if r[0].endswith("index.html"):
                base_path = r[0][: -len("index.html")]
                redirects.extend([(base_path, r[1]), (base_path[:-1], r[1])])

        return [
            {"source": r[0], "target": r[1], "_build_ref": build_commit, "_build_time": build_time} for r in redirects
        ]

    @property
    def _content(self) -> str:
        """
        Generate CSV output.

        Where row 0 is a header row.
        """
        data = self._data
        if not data:
            return ""

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue().rstrip("\r\n")

    @cached_property
    def content(self) -> list[SiteContent]:
        """Output content for site."""
        return [SiteContent(content=self._content, path=Path("-") / "redirects.csv", media_type="text/csv")]
