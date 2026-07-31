import json
from pathlib import Path
from typing import TYPE_CHECKING

from lantern.models.checks import CheckType
from lantern.models.site import ExportMeta, SiteContent, SiteRedirect
from lantern.outputs.base import OutputSite

if TYPE_CHECKING:
    import logging


class SiteHealthOutput(OutputSite):
    """
    Site health check output.

    Requires a record select method for calculating the number of records in the catalogue site.

    Generates a health and monitoring endpoint as static JSON.
    """

    def __init__(
        self, logger: logging.Logger, meta: ExportMeta, site_records_count: int, search_records_count: int
    ) -> None:
        super().__init__(logger=logger, meta=meta, name="Site Health", check_type=CheckType.SITE_HEALTH)
        self._health_path = Path("static") / "json" / "health.json"
        self._site_records_count = site_records_count
        self._search_records_count = search_records_count

    @property
    def _content(self) -> str:
        """
        Generate API Health Check as a JSON document.

        Includes the number of records within the store as a guard against an empty catalogue.

        [1] https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check
        """
        return json.dumps(
            {
                "status": "pass",
                "version": "1",
                "releaseId": f"{self._meta.version}",
                "notes": [
                    "This endpoint is intended for both liveness and readiness checks.",
                    f"It is a static resource, representing the health of this service at: {self._meta.build_time.isoformat()}.",
                ],
                "description": "Health of BAS Data Catalogue (Lantern)",
                "checks": {
                    "site:records": {
                        "componentId": "Site records",
                        "componentType": "datastore",
                        "observedValue": self._site_records_count,
                        "observedUnit": "records",
                        "status": "pass",
                        "affectedEndpoints": [f"{self._meta.base_url}/records/{{fileIdentifier}}.json"],
                        "time": f"{self._meta.build_time.isoformat()}",
                    },
                    "search:records": {
                        "componentId": "Search records",
                        "componentType": "datastore",
                        "observedValue": self._search_records_count,
                        "observedUnit": "records",
                        "status": "pass",
                        "affectedEndpoints": [f"{self._meta.base_url}/search"],
                        "time": f"{self._meta.build_time.isoformat()}",
                    },
                },
                "links": {
                    "about": "https://github.com/antarctica/lantern",
                    "describedby": f"https://github.com/antarctica/lantern/blob/v{self._meta.version}/docs/monitoring.md#health-check-endpoint",
                },
            },
            indent=2,
            ensure_ascii=False,
        )

    @property
    def content(self) -> list[SiteContent]:
        """Output content for site."""
        return [
            SiteContent(content=self._content, path=self._health_path, media_type="application/health+json"),
            SiteRedirect(path=Path("-") / "health", target=self._meta.base_url + "/" + str(self._health_path)),
        ]
