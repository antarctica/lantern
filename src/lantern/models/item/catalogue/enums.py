from enum import Enum


class ResourceTypeLabel(Enum):
    """Partial mapping of the Hierarchy Level code list to friendlier terms."""

    COLLECTION = "COLLECTION"
    DATASET = "DATASET"
    PRODUCT = "PRODUCT (MAP)"
    PAPER_MAP_PRODUCT = "PRODUCT (PAPER MAP)"


class ResourceTypeIcon(Enum):
    """Partial mapping of the Hierarchy Level code list against Font Awesome icon classes."""

    COLLECTION = "fa-fw far fa-shapes"
    DATASET = "fa-fw far fa-cube"
    PRODUCT = "fa-fw far fa-map"
    PAPER_MAP_PRODUCT = "fa-fw far fa-map"


class DistributionType(Enum):
    """Catalogue specific distribution types."""

    ARCGIS_FEATURE_LAYER = "ArcGIS Feature Layer"
    ARCGIS_OGC_FEATURE_LAYER = "OGC API Features (ArcGIS)"
    ARCGIS_VECTOR_TILE_LAYER = "ArcGIS Vector Tile Layer"
    GEOJSON = "GeoJSON"
    GEOPACKAGE = "GeoPackage"
    GEOPACKAGE_ZIP = "GeoPackage (Zipped)"
    JPEG = "JPEG"
    PDF = "PDF"
    PDF_GEO = "PDF (Georeferenced)"
    PNG = "PNG"
    SHAPEFILE_ZIP = "Shapefile (Zipped)"
    X_PAPER_MAP = "Flat or folded paper map"


class Licence(Enum):
    """Supported catalogue licences."""

    OGL_UK_3_0 = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    CC_BY_4_0 = "https://creativecommons.org/licenses/by/4.0/"
    X_ALL_RIGHTS_RESERVED_1 = "https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/"
    X_OPERATIONS_MAPPING_1 = "https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/"
