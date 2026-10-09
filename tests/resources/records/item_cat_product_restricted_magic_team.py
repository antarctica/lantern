from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Constraints,
    Contact,
    ContactIdentity,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Distributions,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import (
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import MAGIC_TEAM as MAGIC_TEAM_PERMISSION
from lantern.lib.metadata_library.models.record.presets.constraints import MAGIC_PRODUCTS_V1, MAGIC_TEAM
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from tests.resources.admin_keys import test_keys
from tests.resources.records.utils import make_record, relate_records

# A restricted record for testing a catalogue item restricted to MAGIC.

record = make_record(
    open_access=False,
    file_identifier="3b08401d-3dbb-4751-a930-21ca0eced88b",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product restricted to MAGIC Team",
    abstract="Item to test a Product configured as restricted to MAGIC team members is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_records(record.file_identifier, groups=["restrictions"]))

# change access and licence
record.identification.constraints = Constraints([MAGIC_TEAM, MAGIC_PRODUCTS_V1])
# add admin metadata to reflect access
keys = test_keys()
admin = AdministrationMetadata(id=record.file_identifier, resource_permissions=[MAGIC_TEAM_PERMISSION])
set_admin(keys=keys, record=record, admin_meta=admin)

# add example distribution to test restricted state handling
distributor = Contact(
    organisation=ContactIdentity(
        name="Mapping and Geographic Information Centre, British Antarctic Survey",
        href="https://ror.org/01rhff309",
        title="ror",
    ),
    phone="+44 (0)1223 221400",
    email="magic@bas.ac.uk",
    address=Address(
        delivery_point="British Antarctic Survey, High Cross, Madingley Road",
        city="Cambridge",
        administrative_area="Cambridgeshire",
        postal_code="CB3 0ET",
        country="United Kingdom",
    ),
    online_resource=OnlineResource(
        href="https://www.bas.ac.uk/teams/magic",
        title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
        description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.DISTRIBUTOR},
)
record.distribution = Distributions(
    [
        Distribution(
            distributor=distributor,
            format=Format(
                format="ArcGIS 3D Scene Layer",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+scene",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="s",
                    function=OnlineResourceFunctionCode.INFORMATION,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS 3D scene layer.",
                )
            ),
        ),
        Distribution(
            distributor=distributor,
            format=Format(
                format="ArcGIS 3D Scene Service",
                href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+scene",
            ),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="s",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="ArcGIS Online",
                    description="Access information as an ArcGIS 3D scene service.",
                )
            ),
        ),
        Distribution(
            distributor=distributor,
            format=Format(
                format="GeoJSON",
                href="https://www.iana.org/assignments/media-types/application/geo+json",
            ),
            transfer_option=TransferOption(
                size=Size(unit="bytes", magnitude=24 * 1024 * 1024),
                online_resource=OnlineResource(
                    href="x",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="GeoJSON",
                    description="Access information as a GeoJSON file.",
                ),
            ),
        ),
        Distribution(
            distributor=distributor,
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href="sftp://san.nerc-bas.ac.uk/data/x",
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                    title="Access from the BAS SAN",
                ),
            ),
        ),
    ]
)
