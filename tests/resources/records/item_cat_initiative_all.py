from datetime import date

from lantern.lib.metadata_library.models.record.elements.common import (
    Date,
    Dates,
    Identifier,
    Identifiers,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    HierarchyLevelCode,
)
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.resources.admin_keys import test_keys
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with all supported fields for initiatives.

initiative_members = ["30825673-6276-4e5a-8a97-f97f2094cd25"]

abstract = """
I spent so much time making sweet jam in the kitchen that it's hard to hear anything over the clatter of the
tin bath. I shall hide behind the couch. _(Guy's a pro.)_

Interfere? Michael: I'm sorry, have we met? She calls it a mayonegg. The only thing more terrifying than the
escaped lunatic's hook was his twisted call…

> Heyyyyy campers!

I didn't get into this business to please sophomore Tracy Schwartzman, so… onward and upward. On… Why, Tracy?! Why?!!

* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

No, I was ashamed to be **SEEN** with you. I like being **WITH** you.

1. Chickens don't clap!
2. Am I in two thirds of a hospital room?

You're a good guy, mon frere. That means brother in French. I don't know how I know that. I took four years of Spanish.

See [here](#) for more good stuff.

The guy runs a prison, he can have any piece of cake he wants. In fact, it was a box of Oscar's legally obtained
medical marijuana. Primo bud. Real sticky weed. So, what do you say? We got a basket full of father-son fun here.
What's Kama Sutra oil? Maybe it's not for us. He… she… what's the difference? Oh hear, hear. In the dark, it all looks
the same. Well excuse me, Judge Reinhold!
"""

record = make_record(
    file_identifier="fd126357-0f88-4b89-81b8-fe33654ef045",
    hierarchy_level=HierarchyLevelCode.INITIATIVE,
    title="Test Resource - Initiative with all supported fields",
    abstract=abstract,
    purpose="Item to test all supported Initiative properties are recognised and presented correctly.",
)
record.identification.dates = Dates(
    creation=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.YEAR),
    publication=Date(date=date(2023, 10, 1)),
    revision=Date(date=date(2023, 10, 1)),
    adopted=Date(date=date(2023, 10, 1)),
    deprecated=Date(date=date(2023, 10, 1)),
    distribution=Date(date=date(2023, 10, 1)),
    expiry=Date(date=date(2023, 10, 1)),
    in_force=Date(date=date(2023, 10, 1)),
    last_revision=Date(date=date(2023, 10, 1)),
    last_update=Date(date=date(2023, 10, 1)),
    next_update=Date(date=date(2023, 10, 1)),
    released=Date(date=date(2023, 10, 1), precision=DatePrecisionCode.MONTH),
    superseded=Date(date=date(2023, 10, 1)),
    unavailable=Date(date=date(2023, 10, 1)),
    validity_begins=Date(date=date(2023, 10, 1)),
    validity_expires=Date(date=date(2023, 10, 1)),
)
record.identification.identifiers = Identifiers(
    [
        Identifier(
            identifier="fd126357-0f88-4b89-81b8-fe33654ef045",
            href=f"https://{CATALOGUE_NAMESPACE}/items/fd126357-0f88-4b89-81b8-fe33654ef045",
            namespace=CATALOGUE_NAMESPACE,
        ),
        Identifier(
            identifier="projects/test123",
            href=f"https://{CATALOGUE_NAMESPACE}/projects/test123",
            namespace=ALIAS_NAMESPACE,
        ),
        Identifier(
            identifier="projects/test123alt",
            href=f"https://{CATALOGUE_NAMESPACE}/projects/test123alt",
            namespace=ALIAS_NAMESPACE,
        ),
        Identifier(
            identifier="10.123/fd126357-0f88-4b89-81b8-fe33654ef045",
            href="https://doi.org/10.123/fd126357-0f88-4b89-81b8-fe33654ef045",
            namespace="doi",
        ),
        Identifier(
            identifier="10.123/test-i-123",
            href="https://doi.org/10.123/test-i-123",
            namespace="doi",
        ),
    ]
)
record.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            description="Overview",
            href="https://images.unsplash.com/vector-1749138851728-3bbb7a3d5c2f?w=360&h=360&auto=format&fit=crop&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            mime_type="image/png",
        )
    ]
)

# reset aggregations to add project members
record.identification.aggregations = Aggregations([])
for initiative_member in initiative_members:
    record.identification.aggregations.append(
        Aggregation(
            identifier=Identifier(
                identifier=initiative_member,
                href=f"https://{CATALOGUE_NAMESPACE}/items/{initiative_member}",
                namespace=CATALOGUE_NAMESPACE,
            ),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.PROJECT,
        ),
    )
# re-add a containing collection
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            href=f"https://{CATALOGUE_NAMESPACE}/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
        initiative_type=AggregationInitiativeCode.COLLECTION,
    )
)
# add a peer project
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="c31720da-8c10-496a-893d-f003f09151e9",
            href=f"https://{CATALOGUE_NAMESPACE}/items/c31720da-8c10-496a-893d-f003f09151e9",
            namespace=CATALOGUE_NAMESPACE,
        ),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
        initiative_type=AggregationInitiativeCode.PROJECT,
    )
)
# Can't add a superseded peer as no suitable target (is added in max product)
# Can't add opposite side relation as not a physical map side
# Can't add a parent physical map as not a physical map side

keys = test_keys()
administration = get_admin(keys=keys, record=record)
administration.gitlab_issues = ["https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123"]
set_admin(keys=keys, record=record, admin_meta=administration)
