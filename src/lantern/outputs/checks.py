import json
import logging
from pathlib import Path

import cattrs

from lantern.models.checks import Check, CheckState, CheckType
from lantern.models.site import ExportMeta, SiteContent
from lantern.outputs.base import OutputSite
from lantern.utils import prettify_html


class ChecksOutput(OutputSite):
    """
    Checks report output.

    Processes a set of completed checks into a report with calculated statistics and overall result.

    Generates a formatted page for manual review and data file for automatic review and/or further processing.
    """

    def __init__(self, logger: logging.Logger, meta: ExportMeta, checks: list[Check]) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Index", check_type=CheckType.NONE)
        self._checks = checks
        self._template_path = "_views/-/checks.html.j2"

        self._site_types = [
            CheckType.SITE_404,
            CheckType.SITE_API,
            CheckType.SITE_HEALTH,
            CheckType.SITE_INDEX,
            CheckType.SITE_PAGES,
            CheckType.SITE_RESOURCES,
            CheckType.WAF_PAGES,
            CheckType.BAS_WEBSITE_SEARCH,
        ]
        self._resource_types = [
            CheckType.ITEM_ALIASES,
            CheckType.ITEM_PAGES,
            CheckType.RECORD_PAGES_JSON,
            CheckType.RECORD_PAGES_HTML,
            CheckType.RECORD_PAGES_XML,
        ]

    @property
    def _object_meta(self) -> dict[str, str]:
        """Key-value metadata to include alongside output content where supported."""
        meta = {"build_key": self._meta.build_key}
        if self._meta.build_repo_ref:
            meta["build_ref"] = self._meta.build_repo_ref
        return meta

    def _process(self) -> tuple[float, bool, dict[CheckState, int], list[CheckState], dict[str, list[Check]]]:
        """Process check results."""
        duration = 0
        pass_fail = False
        stats = dict.fromkeys(CheckState, 0)
        site_checks = []
        resource_checks = {}

        for check in self._checks:
            stats[check.state] += 1
            duration += check.duration

            if check.type in self._site_types:
                site_checks.append(check)
                continue
            if check.file_identifier not in resource_checks:
                resource_checks[check.file_identifier] = []
            resource_checks[check.file_identifier].append(check)
        if stats[CheckState.FAILED] == 0:
            pass_fail = True

        return duration, pass_fail, stats, site_checks, resource_checks

    @property
    def _data(self) -> dict:
        """Assemble checks data."""
        converter = cattrs.Converter()
        duration, pass_fail, stats, site_checks, resource_checks = self._process()

        commit: dict | None = converter.unstructure(self._meta.build_ref) if self._meta.build_ref else None
        if commit:
            commit.pop("external", None)

        return {
            "base_url": self._meta.base_url,
            "commit": commit,
            "time": self._meta.build_time.isoformat(),
            "duration": duration,
            "pass_fail": pass_fail,
            "stats": {label.value: value for label, value in stats.items() if label != CheckState.PENDING},
            "site_checks": converter.unstructure(site_checks),
            "resource_checks": converter.unstructure(resource_checks),
        }

    @property
    def _report(self) -> str:
        """Generate report page."""
        self._meta.html_title = "Verification Checks"
        raw = self._jinja.get_template(self._template_path).render(meta=self._meta.site_metadata, data=self._data)
        return prettify_html(raw)

    @property
    def content(self) -> list[SiteContent]:
        """Output content for site."""
        return [
            SiteContent(
                content=json.dumps(self._data, indent=2, ensure_ascii=False),
                path=Path("-") / "checks" / "data.json",
                media_type="application/json",
            ),
            SiteContent(
                content=self._report,
                path=Path("-") / "checks" / "index.html",
                media_type="text/html",
                object_meta=self._object_meta,
            ),
        ]

    @property
    def checks(self) -> list[Check]:
        """
        Output checks.

        Not applicable to this output.
        """
        return []
