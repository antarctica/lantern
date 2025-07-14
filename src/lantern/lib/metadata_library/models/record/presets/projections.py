from datetime import date

from lantern.lib.metadata_library.models.record.elements.common import (
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    OnlineResource,
)
from lantern.lib.metadata_library.models.record.elements.projection import Code, ReferenceSystemInfo
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode


def make_epsg_projection(code: str) -> ReferenceSystemInfo:
    """Make a CRS info element for an EPSG projection code."""
    return ReferenceSystemInfo(
        code=Code(
            value=f"urn:ogc:def:crs:EPSG::{code}",
            href=f"http://www.opengis.net/def/crs/EPSG/0/{code}",
        ),
        version="6.18.3",
        authority=Citation(
            title="European Petroleum Survey Group (EPSG) Geodetic Parameter Registry",
            dates=Dates(publication=Date(date=date(2008, 11, 12))),
            contacts=Contacts(
                [
                    Contact(
                        organisation=ContactIdentity(name="European Petroleum Survey Group"),
                        email="EPSGadministrator@iogp.org",
                        online_resource=OnlineResource(
                            href="https://www.epsg-registry.org/",
                            title="EPSG Geodetic Parameter Dataset",
                            description="The EPSG Geodetic Parameter Dataset is a structured dataset of Coordinate Reference Systems and Coordinate Transformations, accessible through this online registry.",
                            function=OnlineResourceFunctionCode.INFORMATION,
                        ),
                        role=[ContactRoleCode.PUBLISHER],
                    )
                ]
            ),
        ),
    )


EPSG_4326 = make_epsg_projection("4326")
