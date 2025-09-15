# Lantern - Access

## Static site

A website is available for end-users to browse and view catalogue records.

Endpoints:

- `http://data.bas.ac.uk/-/index/`

> [!NOTE]
> Records are presented as non-standard HTML item pages by default. Links are available from the
> 'Additional Information' tab to view records in various other formats and encodings, including ISO 19139-2:2012 XML.

## Web Accessible Folder

A Web Accessible Folder (WAF) is available for harvesting all catalogue records as ISO 19139-2:2012 XML programmatically.

Endpoints:

- `http://data.bas.ac.uk/waf/iso-19139-all/`

> [!NOTE]
> These records make regular use of `gmx:Anchor` elements over `gco:CharacterString` elements to include relevant URIs.
