from enum import Enum


class AggregationAssociationCode(Enum):
    """
    Aggregation Association code list.

    Schema definition: association_type [1]
    ISO element: DS_AssociationTypeCode [2]

    Contains additional local codes.

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L84
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#DS_AssociationTypeCode
    """

    COLLECTIVE_TITLE = "collectiveTitle"
    CROSS_REFERENCE = "crossReference"
    DEPENDENCY = "dependency"
    IS_COMPOSED_OF = "isComposedOf"
    LARGER_WORK_CITATION = "largerWorkCitation"
    PART_OF_SEAMLESS_DATABASE = "partOfSeamlessDatabase"
    REVISION_OF = "revisionOf"
    SERIES = "series"
    STEREO_MATE = "stereoMate"
    PHYSICAL_REVERSE_OF = "physicalReverseOf"  # local code


class AggregationInitiativeCode(Enum):
    """
    Aggregation Initiative code list.

    Schema definition: initiative_type [1]
    ISO element: DS_InitiativeTypeCode [2]

    Contains additional local codes.

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L104C18-L104
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#DS_InitiativeTypeCode
    """

    CAMPAIGN = "campaign"
    COLLECTION = "collection"
    EXERCISE = "exercise"
    EXPERIMENT = "experiment"
    INVESTIGATION = "investigation"
    MISSION = "mission"
    OPERATION = "operation"
    PLATFORM = "platform"
    PROCESS = "process"
    PROGRAM = "program"
    PROJECT = "project"
    SENSOR = "sensor"
    STUDY = "study"
    TASK = "task"
    TRIAL = "trial"
    DATA_DICTIONARY = "dataDictionary"
    SCIENCE_PAPER = "sciencePaper"
    USER_GUIDE = "userGuide"
    PAPER_MAP = "paperMap"  # local code


class ContactRoleCode(Enum):
    """
    Contact Role code list.

    Schema definition: role [1]
    ISO element: CI_RoleCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L324
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#CI_RoleCode
    """

    AUTHOR = "author"
    CUSTODIAN = "custodian"
    DISTRIBUTOR = "distributor"
    ORIGINATOR = "originator"
    OWNER = "owner"
    POINT_OF_CONTACT = "pointOfContact"
    PRINCIPAL_INVESTIGATOR = "principalInvestigator"
    PROCESSOR = "processor"
    PUBLISHER = "publisher"
    RESOURCE_PROVIDER = "resourceProvider"
    SPONSOR = "sponsor"
    USER = "user"
    CO_AUTHOR = "coAuthor"
    COLLABORATOR = "collaborator"
    CONTRIBUTOR = "contributor"
    EDITOR = "editor"
    FUNDER = "funder"
    MEDIATOR = "mediator"
    RIGHTS_HOLDER = "rightsHolder"
    STAKEHOLDER = "stakeholder"


class ConstraintRestrictionCode(Enum):
    """
    Constraint Restriction code list.

    Schema definition: restriction_code [1]
    ISO element: MD_RestrictionCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1464
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#MD_RestrictionCode
    """

    LICENSE = "license"
    RESTRICTED = "restricted"
    UNRESTRICTED = "unrestricted"


class ConstraintTypeCode(Enum):
    """
    Constraint Type meta code list.

    Schema definition: constraint_type [1]
    ISO element: N/A [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L243
    [2] -
    """

    ACCESS = "access"
    USAGE = "usage"


class DateTypeCode(Enum):
    """
    Date Type code list.

    Schema definition: dates [1]
    ISO element: CI_DateTypeCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L437
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#CI_DateTypeCode
    """

    CREATION = "creation"
    PUBLICATION = "publication"
    REVISION = "revision"
    ADOPTED = "adopted"
    DEPRECATED = "deprecated"
    DISTRIBUTION = "distribution"
    EXPIRY = "expiry"
    IN_FORCE = "inForce"
    LAST_REVISION = "lastRevision"
    LAST_UPDATE = "lastUpdate"
    NEXT_UPDATE = "nextUpdate"
    RELEASED = "released"
    SUPERSEDED = "superseded"
    UNAVAILABLE = "unavailable"
    VALIDITY_BEGINS = "validityBegins"
    VALIDITY_EXPIRES = "validityExpires"


class DatePrecisionCode(Enum):
    """
    Date Precision meta code list.

    Precision of the date value to workaround Python minimum date precision of day (which may not be known).

    Schema definition: N/A [1]
    ISO element: N/A [2]

    [1] -
    [2] -
    """

    MONTH = "month"
    YEAR = "year"


class HierarchyLevelCode(Enum):
    """
    Hierarchical Level code list.

    Schema definition: hierarchy_level [1]
    ISO element: MD_ScopeCode [2]

    Contains additional local codes.

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L826C10-L826C25
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#MD_ScopeCode
    """

    AGGREGATE = "aggregate"
    APPLICATION = "application"
    ATTRIBUTE = "attribute"
    ATTRIBUTE_TYPE = "attributeType"
    COLLECTION = "collection"
    COLLECTION_HARDWARE = "collectionHardware"
    COLLECTION_SESSION = "collectionSession"
    COVERAGE = "coverage"
    DATASET = "dataset"
    DIMENSION_GROUP = "dimensionGroup"
    DOCUMENT = "document"
    FEATURE = "feature"
    FEATURE_TYPE = "featureType"
    FIELD_SESSION = "fieldSession"
    INITIATIVE = "initiative"
    METADATA = "metadata"
    MODEL = "model"
    NON_GEOGRAPHIC_DATASET = "nonGeographicDataset"
    PRODUCT = "product"
    PROPERTY_TYPE = "propertyType"
    REPOSITORY = "repository"
    SAMPLE = "sample"
    SERIES = "series"
    SERVICE = "service"
    SOFTWARE = "software"
    TILE = "tile"

    # Local
    MAP_PRODUCT = "mapProduct"
    PAPER_MAP_PRODUCT = "paperMapProduct"
    WEB_MAP_PRODUCT = "webMapProduct"


class MaintenanceFrequencyCode(Enum):
    """
    Maintenance Frequency code list.

    Schema definition: maintenance_frequency [1]
    ISO element: MD_MaintenanceFrequencyCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1123C18-L1123
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#MD_MaintenanceFrequencyCode
    """

    CONTINUAL = "continual"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUALLY = "biannually"
    ANNUALLY = "annually"
    AS_NEEDED = "asNeeded"
    IRREGULAR = "irregular"
    NOT_PLANNED = "notPlanned"
    UNKNOWN = "unknown"


class OnlineResourceFunctionCode(Enum):
    """
    Online Function code list.

    Schema definition: online_resource [1]
    ISO element: CI_OnLineFunctionCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1205
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#CI_OnLineFunctionCode
    """

    DOWNLOAD = "download"
    INFORMATION = "information"
    OFFLINE_ACCESS = "offlineAccess"
    ORDER = "order"
    SEARCH = "search"


class ProgressCode(Enum):
    """
    Progress code list.

    Schema definition: progress [1]
    ISO element: MD_ProgressCode [2]

    [1] https://github.com/antarctica/metadata-library/blob/v0.15.1/src/bas_metadata_library/schemas/dist/iso_19115_2_v4.json#L1340
    [2] https://wiki.esipfed.org/ISO_19115-3_Codelists#MD_ProgressCode
    """

    COMPLETED = "completed"
    HISTORICAL_ARCHIVE = "historicalArchive"
    OBSOLETE = "obsolete"
    ON_GOING = "onGoing"
    PLANNED = "planned"
    REQUIRED = "required"
    UNDER_DEVELOPMENT = "underDevelopment"
