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
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with all supported fields for collections.

collection_members = [
    "30825673-6276-4e5a-8a97-f97f2094cd25",
    "f90013f6-2893-4c72-953a-a1a6bc1919d7",
    "e0df252c-fb8b-49ff-9711-f91831b66ea2",
    "589408f0-f46b-4609-b537-2f90a2f61243",
    "4ba929ac-ca32-4932-a15f-38c1640c0b0f",
    "5ab58461-5ba7-404d-a904-2b4efcb7556e",
    "c993ea2b-d44e-4ca0-9007-9a972f7dd117",
    "53ed9f6a-2d68-46c2-b5c5-f15422aaf5b2",
    "3c77ffae-6aa0-4c26-bc34-5521dbf4bf23",
    "57327327-4623-4247-af86-77fb43b7f45b",
    "09dbc743-cc96-46ff-8449-1709930b73ad",
]

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
    file_identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
    hierarchy_level=HierarchyLevelCode.COLLECTION,
    title="Test Resource - Collection with all supported fields",
    abstract=abstract,
    purpose="Item to test all supported Collection properties are recognised and presented correctly.",
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
            identifier="dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            href="https://data.bas.ac.uk/items/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            namespace="data.bas.ac.uk",
        ),
        Identifier(
            identifier="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
            href="https://gitlab.data.bas.ac.uk/MAGIC/test/-/issues/123",
            namespace="gitlab.data.bas.ac.uk",
        ),
        Identifier(
            identifier="collections/test123",
            href="https://data.bas.ac.uk/collections/test123",
            namespace="alias.data.bas.ac.uk",
        ),
        Identifier(
            identifier="collections/test123alt",
            href="https://data.bas.ac.uk/collections/test123alt",
            namespace="alias.data.bas.ac.uk",
        ),
        Identifier(
            identifier="10.123/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            href="https://doi.org/10.123/dbe5f712-696a-47d8-b4a7-3b173e47e3ab",
            namespace="doi",
        ),
        Identifier(
            identifier="10.123/test123",
            href="https://doi.org/10.123/test123",
            namespace="doi",
        ),
    ]
)
record.identification.graphic_overviews = GraphicOverviews(
    [
        GraphicOverview(
            identifier="overview",
            description="Overview",
            href="https://images.unsplash.com/photo-1603738397364-e89b419504d0?w=360&h=360&auto=format&fit=crop&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            mime_type="image/png",
        )
    ]
)

# reset collection members
record.identification.aggregations = Aggregations([])
for collection_member in collection_members:
    record.identification.aggregations.append(
        Aggregation(
            identifier=Identifier(
                identifier=collection_member,
                href=f"https://data.bas.ac.uk/items/{collection_member}",
                namespace="data.bas.ac.uk",
            ),
            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        ),
    )
# add a related collection
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(
            identifier="8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
            href="https://data.bas.ac.uk/items/8fd6a7cc-e696-4a82-b5f6-fb04dfa4cbea",
            namespace="data.bas.ac.uk",
        ),
        association_type=AggregationAssociationCode.CROSS_REFERENCE,
        initiative_type=AggregationInitiativeCode.COLLECTION,
    )
)
