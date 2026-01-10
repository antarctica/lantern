# Lantern - Access

## Website

A website is available for end-users to browse and view catalogue records as HTML formatted items at:

- `http://data.bas.ac.uk/-/index/`

> [!TIP]
> See the 'Additional Information' tab for links to view records in other formats and encodings, including ISO
> 19139-2:2012 XML.

## API catalog

A [RFC 9727 API Catalog](https://datatracker.ietf.org/doc/html/rfc9727) describes the entrypoints and accompanying
documentation for the data catalogue available at:

- `http://data.bas.ac.uk/.well-known/api-catalog`

## Web Accessible Folder

A [Web Accessible Folder (WAF)](https://ioos.github.io/catalog/pages/registry/waf_creation/) is available for
harvesting all catalogue records as ISO 19139-2:2012 XML programmatically.

Endpoints:

- `http://data.bas.ac.uk/waf/iso-19139-all/`

> [!NOTE]
> These records make regular use of `gmx:Anchor` elements over `gco:CharacterString` elements to include relevant URIs.
