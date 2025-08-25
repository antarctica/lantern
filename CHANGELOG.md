# Lantern - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Wherever possible, a reference to an issue in the project issue tracker should be included to give additional context.

<!-- pyml disable no-duplicate-heading,no-duplicate-header -->
## [Unreleased]

### Added

* Markdown linting for project documentation

## [0.2.1] - 2025-08-22

### Added

* Type checking using Astral Ty

### Changed

* Various fixes from enabling static type checking

## [0.2.0] - 2025-08-22

### Added

* Pickled records in the GitLab store cache for improved performance
* Data Protection Impact Assessment (DPIA)
* Initial support to export select items into the Public Website global search
* Admonition support for tips, warnings in markdown supported record abstracts, etc.
* Initial dark mode styling
* Record Revision support
* Accessibility statement
* Adding file identifier and revision metadata to published S3 objects
* Showing item aliases in additional information section
* Showing a page build/render time in additional information section
* Support for item cross-references in related items section
* Initial support for items a record supersedes in related items section
* Markdown formatting guide
* Validation styles for item contact forms (invalid only)
* Support for ArcGIS Raster (Map) distribution options

### Fixed

* Missing padding on legal pages when viewed on mobile
* Fallback feedback link shown where JavaScript is disabled
* Fallback static sections for distribution options shown where JavaScript is disabled
* Incorrect Sentry DSN
* Inconsistent padding within item tabs
* Accessibility improvements for invalid contact form fields and link underlining

### Changed

* Split GitLab Store into `GitLabStore` and `GitLabLocalCache` for better structure
* Upgraded dependencies
* Improved template composition to reduce repetition
* Refactoring alias and catalogue namespace references into constants
* Improved test records to cover additional property combinations
* Improved item summaries to prevent showing 'None' for an empty summary
* Restricting item related tab to Catalogue items via namespace filtering
* Always underline links on pages for better accessibility given poor colour contrast

### Removed

* Record and item summary classes (except for `ItemCatalogueSummary`) to reduce unnecessary complexity

## [0.1.1] - 2025-07-23

### Added

* Continuous Integration

## [0.1.0] - 2024-07-22

### Added

* Initial implementation based on the [BAS Assets Tracking Service v0.7.0 release](https://github.com/antarctica/assets-tracking-service/tree/v0.7.0)
<!-- pyml enable no-duplicate-heading,no-duplicate-header) -->
