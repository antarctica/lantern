from enum import Enum


class ItemSuperType(Enum):
    """
    High-level grouping of ResourceType members.

    To distinguish between:
     - 'container' items that group other items (collections, projects, etc.)
    - 'resource' items represent actual data holdings (datasets, products, etc.)
    """

    CONTAINER = "container"
    RESOURCE = "resource"


class ResourceTypeIcon(Enum):
    """Partial mapping of the Hierarchy Level code list against Font Awesome icon classes."""

    COLLECTION = "fa-regular fa-shapes"
    DATASET = "fa-regular fa-cube"
    INITIATIVE = "fa-regular fa-cassette-betamax"
    PRODUCT = "fa-regular fa-file-fragment"
    MAP_PRODUCT = "fa-regular fa-frame"
    PAPER_MAP_PRODUCT = "fa-regular fa-map"
    WEB_MAP_PRODUCT = "fa-regular fa-picture-in-picture"


class DistributionType(Enum):
    """Catalogue specific distribution types."""

    ARCGIS_FEATURE_LAYER = "ArcGIS Feature Layer"
    ARCGIS_OGC_FEATURE_LAYER = "OGC API Features (ArcGIS)"
    ARCGIS_RASTER_TILE_LAYER = "ArcGIS Raster Tile Layer"
    ARCGIS_VECTOR_TILE_LAYER = "ArcGIS Vector Tile Layer"
    CSV = "CSV"
    FPL = "FPL"
    GEOJSON = "GeoJSON"
    GEOPACKAGE = "GeoPackage"
    GEOPACKAGE_ZIP = "GeoPackage (Zipped)"
    GPX = "GPX"
    JPEG = "JPEG"
    MAPBOX_VECTOR_TILE = "MapBox Vector Tiles (MBTile)"
    PDF = "PDF"
    PDF_GEO = "PDF (Georeferenced)"
    PNG = "PNG"
    SHAPEFILE_ZIP = "Shapefile (Zipped)"
    X_BAS_PAPER_MAP = "Flat or folded paper map"
    X_BAS_SAN = "SAN path reference"


class Licence(Enum):
    """Supported resource licences."""

    OGL_UK_3_0 = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    CC_BY_4_0 = "https://creativecommons.org/licenses/by/4.0/"
    X_ALL_RIGHTS_RESERVED_1 = "https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/"
    X_OPERATIONS_MAPPING_1 = "https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/"
    X_MAGIC_PRODUCTS_1 = "https://metadata-resources.data.bas.ac.uk/licences/magic-products-v1/"
