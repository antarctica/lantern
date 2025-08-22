# BAS Assets Tracking Service - Libraries

Extensions to, or code closely associated with, third-party libraries relied on by this application.

## Markdown

Package: `assets_tracking_service.lib.markdown`

### Markdown plain text plugin

A plugin based on https://github.com/kostyachum/python-markdown-plain-text is used to strip Markdown formatting from
text for use in HTML titles for example.

### Markdown automatic links plugin

A plugin based on https://github.com/daGrevis/mdx_linkify is used to convert inline URLs and email addresses in
Markdown text into HTML links.

### Markdown list formatting plugin

A plugin based on https://gitlab.com/ayblaq/prependnewline/ is used to automatically add additional line breaks to
correctly paragraphs from lists in Markdown and ensure proper formatting.

## BAS Metadata Library

**Note:** These are rough/working notes that will be written up properly when this module is extracted.

Package: `lantern.lib.metadata_library`

Includes classes for [Records](/docs/data-model.md#records).

These redesigned and refactored classes will replace core parts of the Metadata Library project.

### Adding new Record properties

> [!CAUTION]
> This section is Work in Progress (WIP) and may not be complete/accurate.

To add support for a new ISO element within Records:

1. create a new data class for the new element in the relevant top module (i.e. `identification.py`)
2. define enums for code lists if needed
3. define a cattrs (un)structure hook if needed
4. include the new class as a property in the relevant top-level class (i.e. `Identification`)
5. register the cattrs (un)structure hook in the top-level class hooks if needed
6. add tests for the new class testing all permutations, and cattrs hook if needed
7. amend tests for top-level class (i.e. `TestIdentification`) variant:
	1. add variant for minimal instance of the new class if optional
	2. amend all variants with a minimal instance of the new class if required
	3. amend asserts to check new class as required
	4. amend tests for top-level cattrs hooks if changed
8. if new class part of minimal record, update `fx_record_config_minimal` fixture
9. amend tests for root-level class (i.e. `TestRecord`):
	1. amend tests for root-level cattrs hooks if top-level hooks changed (as an integration check)
	2. amend variants in `test_loop` as needed (include all possible options in complete variant)
10. amend list of unsupported properties in `/docs/data-model.md#record-limitations` as needed
