import json
import logging

from jinja2 import Template
from mypy_boto3_s3 import S3Client

from lantern.config import Config
from lantern.exporters.base import Exporter
from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.enums import AggregationAssociationCode
from lantern.models.item.website.search import ItemWebsiteSearch


class WebsiteSearchExporter(Exporter):
    """
    Proto Public Website search exporter.

    Note: Intended for BAS use only.

    Generates items for inclusion in the search of the BAS public website (www.bas.ac.uk) to aid discovery. These items
    are intended for insertion into the BAS operated API which acts as an aggregator across BAS data catalogues, and
    the endpoint used by the public website sync.

    See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450 for initial implementation and background.

    This exporter filters items to those which are:

    1. open access (based on an `unrestricted` access constraint)
    2. not superseded by another record (based on `RevisionOf` aggregations)

    Due to this second condition, this exporter cannot be implemented as a RecordExporter as foreign records determine
    whether a record is superseded rather than each target record.

    Note: This prototype does not yet insert items into the BAS aggregating API, rather it exports and/or publishes
    items as a static file for testing.

    Note: This prototype additionally (and temporarily) generates, exports and/or publishes a HTML mockup of what these
    items may look as rendered search results in the public website.
    """

    # This template is defined in-line as it won't be used long-term.
    _mockup_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>British Antarctic Survey</title>
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Work+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
  <style>
    .work-sans {
      font-family: "Work Sans", sans-serif;
      font-optical-sizing: auto;
      font-weight: 400;
      font-style: normal;
    }
  </style>
</head>
<body class="bg-white work-sans">
  <nav class="bg-[#013B5C] text-white p-4">
    <div class="container mx-auto flex justify-between items-center">
      <div>
        <img src="https://cdn.web.bas.ac.uk/bas-style-kit/0.7.3/img/logos-symbols/bas-logo-inverse-transparent-64.png" alt="BAS logo" />
      </div>
      <ul class="flex space-x-4">
        <li><a href="#" class="hover:underline">About</a></li>
        <li><a href="#" class="hover:underline">Science</a></li>
        <li><a href="#" class="hover:underline">Data</a></li>
        <li><a href="#" class="hover:underline">Polar Operations</a></li>
        <li><a href="#" class="hover:underline">People</a></li>
        <li><a href="#" class="hover:underline">News & media</a></li>
        <li><a href="#" class="hover:underline">Jobs</a></li>
        <li><a href="#" class="hover:underline">Contact</a></li>
        <li>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"></path>
          </svg>
        </li>
      </ul>
    </div>
  </nav>

  <div class="mx-38 mt-2">
    <p class="text-sm text-gray-600">Home / Search results for “South Georgia”</p>
  </div>

  <main class="mx-68 mt-16 space-y-16">
    {% for item in items %}
      <article class="flex gap-6 items-start">
        <img src="{{ item.thumbnail_href }}" alt="Image" class="w-72 h-48 object-contain flex-shrink-0" />
        <div class="flex flex-col space-y-4">
          <small class="uppercase">{{ item.type }}</small>
          <h1 class="text-2xl font-semibold"><a class="text-[#013B5C]" href="{{ item.href }}">{{ item.title }}</a></h1>
          <div class="text-gray-700">{{ item.description }}</div>
        </div>
      </article>
      <hr class="border-gray-300" />
    {% endfor %}
  </main>
</body>
</html>
    """

    def __init__(self, config: Config, logger: logging.Logger, s3: S3Client) -> None:
        """Initialise exporter."""
        super().__init__(config, logger, s3)
        self._export_path = self._config.EXPORT_PATH / "-" / "public-website-search" / "items.json"
        self._mockup_path = self._export_path.parent / "mockup.html"
        self._records: list[Record] = []

    @property
    def name(self) -> str:
        """Exporter name."""
        return "Public Website search results"

    def loads(self, records: list[Record]) -> None:
        """Populate exporter."""
        self._records = records

    @staticmethod
    def _get_superseded_records(records: list[Record]) -> list[str]:
        """List identifiers of records superseded by other records."""
        supersedes = set()
        for record in records:
            aggregations = record.identification.aggregations.filter(
                namespace="data.bas.ac.uk", associations=AggregationAssociationCode.REVISION_OF
            )
            supersedes.update(aggregations.identifiers())
        return list(supersedes)

    def _filter_items(self, items: list[ItemWebsiteSearch]) -> list[ItemWebsiteSearch]:
        """
        Select in-scope items.

        See https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/450/#note_142966 for initial criteria.
        """
        superseded = self._get_superseded_records(self._records)
        return [item for item in items if item.resource_id not in superseded and item.open_access]

    def _dumps(self) -> str:
        """Generate aggregation API resources for in-scope items."""
        items = [
            ItemWebsiteSearch(record=record, source=self._config.NAME, base_url=self._config.BASE_URL)
            for record in self._records
        ]
        payload = [item.dumps() for item in self._filter_items(items)]
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _dumps_mockup(self) -> str:
        """
        Generate HTML mockup of search results.

        Based on initial public website designs.

        Note: This is a temporary output.
        """
        items = json.loads(self._dumps())
        content = [item["content"] for item in items]
        return Template(self._mockup_template).render(items=content)

    def export(self) -> None:
        """Export aggregation API resources and HTML mockup to directory."""
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        with self._export_path.open("w") as f:
            f.write(self._dumps())
        with self._mockup_path.open("w") as f:
            f.write(self._dumps_mockup())

    def publish(self) -> None:
        """
        Publish aggregation API resources and HTML mockup to S3.

        This is a temporary measure until an agreed interface is available to insert or push these API resources.
        """
        index_key = self._s3_utils.calc_key(self._export_path)
        self._s3_utils.upload_content(key=index_key, content_type="application/json", body=self._dumps())
        mockup_key = self._s3_utils.calc_key(self._mockup_path)
        self._s3_utils.upload_content(key=mockup_key, content_type="text/html", body=self._dumps_mockup())
