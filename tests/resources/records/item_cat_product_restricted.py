from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Constraint,
    Constraints,
    Contact,
    ContactIdentity,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Format,
    Size,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import BAS_STAFF
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from tests.resources.records.admin_keys.testing_keys import load_keys as load_test_keys
from tests.resources.records.utils import make_record, relate_products

# A record for an ItemCatalogue instance with minimum required fields for products.

record = make_record(
    file_identifier="57327327-4623-4247-af86-77fb43b7f45b",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product marked as restricted",
    abstract="Item to test a Product with a restricted access constraint is presented correctly.",
)
# add related peers
record.identification.aggregations.extend(relate_products(record.file_identifier))
record.identification.constraints = Constraints(
    [
        Constraint(
            type=ConstraintTypeCode.ACCESS,
            restriction_code=ConstraintRestrictionCode.RESTRICTED,
            statement="Closed Access",
        ),
        Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/",
            statement="This information is licensed under the (Local) Operations Mapping v1 licence. To view this licence, visit https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/.",
        ),
    ]
)

keys = load_test_keys()
administration = get_admin(keys=keys, record=record)
administration.access_permissions = [BAS_STAFF]
set_admin(keys=keys, record=record, admin_meta=administration)

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

record.distribution = [
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
        format=Format(
            format="PDF",
            href="https://www.iana.org/assignments/media-types/application/pdf",
        ),
        transfer_option=TransferOption(
            size=Size(unit="bytes", magnitude=321 * 1024 * 1024),
            online_resource=OnlineResource(
                href="x",
                function=OnlineResourceFunctionCode.DOWNLOAD,
                title="PDF",
                description="Access information as a PDF file.",
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
