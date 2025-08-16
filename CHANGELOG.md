# Lantern - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Wherever possible, a reference to an issue in the project issue tracker should be included to give additional context.

## [Unreleased]

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

### Fixed

* Missing padding on legal pages when viewed on mobile
* Fallback feedback link shown where JavaScript is disabled
* Fallback static sections for distribution options shown where JavaScript is disabled

### Changed

* Split GitLab Store into `GitLabStore` and `GitLabLocalCache` for better structure
* Upgraded dependencies
* Improving template composition to reduce repetition
* Refactoring alias and catalogue namespace references into constants
* Restricting item related tab to Catalogue items via namespace filtering

### Removed

* Record and item summary classes (except for `ItemCatalogueSummary`) to reduce unnecessary complexity

## [0.1.1] - 2025-07-23

### Added

* Continuous Integration

## [0.1.0] - 2024-07-22

###  Added

* Initial implementation based on the [BAS Assets Tracking Service v0.7.0 release](https://github.com/antarctica/assets-tracking-service/tree/v0.7.0)
