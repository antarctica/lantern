# Lantern - Access

## Website

A [website](http://data.bas.ac.uk/home) is available for end-users to browse catalogue records as HTML formatted items.

> [!TIP]
> See the 'Additional Information' tab in each item page for other metadata representations, including ISO 19139 XML.

### Search

> [!WARNING]
> This section is Work in Progress (WIP) and may not be complete/accurate.

A basic [Items Search](http://data.bas.ac.uk/search) page is available for end-users to query catalogue items.

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

## BAS Public Website Search

A [Subset](/docs/outputs.md#public-website-search-criteria) of catalogue records are included in the
[BAS Public Website](https://www.bas.ac.uk/?post_type=catalogue_record) and can be searched via its
[Global Search](https://www.bas.ac.uk/?s=).
