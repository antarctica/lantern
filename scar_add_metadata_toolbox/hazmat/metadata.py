"""
ISO 19115 Metadata classes/methods

Warning: Here be dragons!

These classes/methods are considered 'hazardous material' meaning they are experimental, inefficient and inelegant.
They are intended to workaround limitations in other packages (in this case the BAS Metadata Library) and from these,
determine changes needed within these packages.

As these classes/methods can change frequently, and are not intended for long term use, they are not covered by tests
and exempted from code coverage (see `.coverage`). As these classes/methods are used to workaround issues, they often
use awkward, non-ideal or 'risky' code that's frowned upon and doesn't follow best practices. In this case, methods are
used to workaround bugs or missing features in the Metadata Library.

Once a solution to a problem is found it should be upstreamed into the relevant package and removed from here. It's
expected that all 'hazmat' classes/methods will eventually be removed as time allows.
"""

from copy import deepcopy
from datetime import date, datetime
from typing import List, Dict

# noinspection PyPackageRequirements
# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import tostring, ElementTree  # nosec

from backports.datetime_fromisoformat import MonkeyPatch

from bas_metadata_library.standards.iso_19115_2_v1 import MetadataRecord, MetadataRecordConfig


# Workaround for lack of `date(time).fromisoformat()` method in Python 3.6
MonkeyPatch.patch_fromisoformat()


def load_record_from_json(record) -> dict:
    """
    Decodes a Metadata Configuration object from JSON

    MetadataConfig instances are objects, using data types such as datetimes. Whilst makes sense at runtime, objects
    are not an ideal format for storing as files (as backups, or for transferring information from system to another
    for example). To solve this a JSON encoding of MetadataConfig objects is used instead, which this method parses to
    reconstruct the original object.

    This encoding only requires encoding dates, however due to other bugs in the Metadata Library, additional fixes are
    applied to some other elements/options.

    Long term, a JSON loads method will be added to the MetadataConfig class. Other issues will be fixed as bugs.
    """

    # hack
    options = {"data": record}

    options["data"]["date_stamp"] = date.fromisoformat(options["data"]["date_stamp"])
    options["data"]["reference_system_info"]["authority"]["dates"][0]["date"] = date.fromisoformat(
        options["data"]["reference_system_info"]["authority"]["dates"][0]["date"]
    )
    for index, resource_date in enumerate(options["data"]["resource"]["dates"]):
        if "date_precision" in resource_date.keys() and resource_date["date_precision"] == "year":
            options["data"]["resource"]["dates"][index]["date"] = date(
                year=int(options["data"]["resource"]["dates"][index]["date"]), month=1, day=1,
            ).isoformat()

        if len(options["data"]["resource"]["dates"][index]["date"]) == 10:
            options["data"]["resource"]["dates"][index]["date"] = date.fromisoformat(
                options["data"]["resource"]["dates"][index]["date"]
            )
        elif len(options["data"]["resource"]["dates"][index]["date"]) == 19:
            options["data"]["resource"]["dates"][index]["date"] = datetime.fromisoformat(
                options["data"]["resource"]["dates"][index]["date"]
            )

    for index, keyword in enumerate(options["data"]["resource"]["keywords"]):
        options["data"]["resource"]["keywords"][index]["thesaurus"]["dates"][0]["date"] = date.fromisoformat(
            options["data"]["resource"]["keywords"][index]["thesaurus"]["dates"][0]["date"]
        )

    if len(options["data"]["resource"]["extent"]["temporal"]["period"]["start"]) == 4:
        options["data"]["resource"]["extent"]["temporal"]["period"][
            "start"
        ] = f"{options['data']['resource']['extent']['temporal']['period']['start']}-01-01"
    options["data"]["resource"]["extent"]["temporal"]["period"]["start"] = datetime.fromisoformat(
        options["data"]["resource"]["extent"]["temporal"]["period"]["start"]
    )
    options["data"]["resource"]["extent"]["temporal"]["period"]["end"] = datetime.fromisoformat(
        options["data"]["resource"]["extent"]["temporal"]["period"]["end"]
    )
    if "measures" in options["data"]["resource"].keys():
        options["data"]["resource"]["measures"][0]["dates"][0]["date"] = date.fromisoformat(
            options["data"]["resource"]["measures"][0]["dates"][0]["date"]
        )

    # hack
    record_data = options["data"]

    record_config = MetadataRecordConfig(**record_data)
    record_config.validate()

    # hack around invalid/missing character encoding
    _record_config = record_config.config
    # noinspection PyTypeChecker
    _record_config["character_set"] = "utf-8"
    _record_config["resource"]["character_set"] = "utf-8"

    # hack ground weird structure of constraints
    if (
        "constraints" in _record_config["resource"].keys()
        and "usage" in _record_config["resource"]["constraints"].keys()
    ):
        _usage_constraints = {}
        for usage_constraint in _record_config["resource"]["constraints"]["usage"]:
            _usage_constraints = {**_usage_constraints, **usage_constraint}

    return _record_config


def dump_record_to_json(record):
    """
    Encodes a Metadata Configuration object as JSON

    MetadataConfig instances are objects, using data types such as datetimes. Whilst makes sense at runtime, objects
    are not an ideal format for storing as files (as backups, or for transferring information from system to another
    for example). To solve this, a JSON encoding of MetadataConfig objects is used instead, implemented by this method
    by encoding dates/datetimes as needed.

    Long term, a JSON dumps method will be added to the MetadataConfig class.
    """

    # Needed because record configs (record parameter in this method) are passed by reference not value, meaning their
    # structure will otherwise be modified (e.g. dates turned into strings). We want to do this in an export but without
    # modifying the original record config object.
    record = deepcopy(record)

    record["date_stamp"] = record["date_stamp"].isoformat()
    record["reference_system_info"]["authority"]["dates"][0]["date"] = record["reference_system_info"]["authority"][
        "dates"
    ][0]["date"].isoformat()

    for index, resource_date in enumerate(record["resource"]["dates"]):
        record["resource"]["dates"][index]["date"] = resource_date["date"].isoformat()

        try:
            if record["resource"]["dates"][index]["date_precision"] == "year":
                _date = date.fromisoformat(resource_date["date"])
                record["resource"]["dates"][index]["date"] = str(_date.year)
        except KeyError:
            pass

    for index, keyword in enumerate(record["resource"]["keywords"]):
        record["resource"]["keywords"][index]["thesaurus"]["dates"][0]["date"] = record["resource"]["keywords"][index][
            "thesaurus"
        ]["dates"][0]["date"].isoformat()

    record["resource"]["extent"]["temporal"]["period"]["start"] = record["resource"]["extent"]["temporal"]["period"][
        "start"
    ].isoformat()
    record["resource"]["extent"]["temporal"]["period"]["end"] = record["resource"]["extent"]["temporal"]["period"][
        "end"
    ].isoformat()

    if "measures" in record["resource"].keys():
        record["resource"]["measures"][0]["dates"][0]["date"] = record["resource"]["measures"][0]["dates"][0][
            "date"
        ].isoformat()

    return record


def generate_xml_record_from_record_config_without_xml_declaration(record_config):
    """
    Encodes a Metadata Record as XML without an XML declaration

    The `make_element` method in MetadataRecord class encodes a MetadataRecord instance as an an XML document (str),
    including an XML declaration.

    This is done for completeness and with the assumption that records will always be standalone files. However when
    CSW transactions are used for example, records will be embedded within a larger document. In this case the
    (additional) declaration will create an invalid/illegal XML document (as only one declaration can be defined at the
    beginning of the overall document).

    This method is essentially the XML same as the `make_element` method but without the XML declaration. However, due
    to other bugs in the Metadata Library, additional fixes are applied to some other elements/options.

    Long term, the XML declaration will made optional in the make_element method. Other issues will be fixed as bugs.
    """

    # hack
    if isinstance(record_config, MetadataRecordConfig):
        record_config = record_config.config

    # hack
    # noinspection PyTypeChecker
    record_config["character_set"] = "utf8"
    record_config["resource"]["character_set"] = "utf8"

    # hack (not sure why this is happening)
    if "value" in record_config["resource"]["formats"][1]:
        record_config["resource"]["formats"][1]["version"] = record_config["resource"]["formats"][1]["value"]
        del record_config["resource"]["formats"][1]["value"]
    if "value" in record_config["resource"]["formats"][2]:
        record_config["resource"]["formats"][2]["version"] = record_config["resource"]["formats"][2]["value"]
        del record_config["resource"]["formats"][2]["value"]

    record_config = MetadataRecordConfig(**record_config)
    record = MetadataRecord(configuration=record_config).make_element()
    document = tostring(ElementTree(record), pretty_print=True, xml_declaration=False, encoding="utf-8")
    return document


def generate_record_config_from_record_xml(record_xml: str, validate_record_config: bool = True) -> dict:
    """
    Converts an XML encoded MetadataRecord instance into a MetadataConfig object

    This conversion is natively supported in the Metadata Library, however, due to other bugs in the Metadata Library,
    additional fixes are applied to some other elements/options.

    Long term, these issues will be fixed as bugs.
    """
    record_config = MetadataRecord(record=record_xml).make_config()
    _record_config = record_config.config

    # hack around date_stamp being a datetime when it should be a date
    try:
        # noinspection PyUnresolvedReferences
        _record_config["date_stamp"] = _record_config["date_stamp"].date()
    except KeyError:
        pass

    # hack around invalid/missing character encoding
    # noinspection PyTypeChecker
    _record_config["character_set"] = "utf-8"
    _record_config["resource"]["character_set"] = "utf-8"

    # hack around wrong key for format versions
    try:
        for index, resource_format in enumerate(_record_config["resource"]["formats"]):
            if "value" in resource_format.keys():
                _record_config["resource"]["formats"][index]["version"] = resource_format["value"]
                del _record_config["resource"]["formats"][index]["value"]
    except KeyError:
        pass

    if validate_record_config:
        record_config.validate()
    return _record_config


def process_usage_constraints(constraints=List[Dict[str, dict]]) -> Dict[str, dict]:
    """
    Convert usage constraints from a list to dictionary

    This is a workaround for the confusing way usage constraints are currently modelled in the Metadata Libraries
    record configuration scheme. This is currently modelled closely on the ISO abstract model, however in practice,
    this is not very intuitive and overly flexible to interpret easily. This str

    This method represents how this structure will work in future to prevent adding additional processing to support
    structures that will be replaced.

    Long term, this new structure will be used natively.
    """
    _constraints = {}
    for constraint in constraints:
        _key = list(constraint.keys())[0]
        _constraints[_key] = constraint[_key]

    return _constraints
