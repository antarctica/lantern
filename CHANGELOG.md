# Lantern - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Wherever possible, a reference to an issue in the project issue tracker should be included to give additional context.

<!-- pyml disable no-duplicate-heading,no-duplicate-header -->
## [Unreleased]

### Added

* Non-interactive record publishing workflow for integrating with other projects hosted on the central workstations
* Dark mode variant of item summary default thumbnail
* Support for CSV, FPL, GPX and MBTile file distribution options
* Support for custom labels and optional descriptions in distribution options
* Bot protection for item enquiry forms
* Infrastructure diagram and hosting information

### Fixed

* Refactoring `ItemBase` to work with Records or Record Revisions (previously required RecordRevision's)
* Invalidating cache where a significant number of commits have occurred since the last update
* Preventing licences unknown to catalogue items breaking exports
* Item thumbnail alt text not describing content by associating with abstract via `aria-details`
* Minimum padding for all device sizes where auto centering would give zero margin

### Changed

* Documentation improvements
* Contextualising items fragment in item summaries for physical map products (sides rather than items)

## [0.3.0] - 2025-09-20

### Added

* Markdown linting for project documentation
* Dev command for bootstrapping a remote GitLab records repo
* Dedicated Catalogue Record class to enforce Catalogue specific requirements
* Support for dynamically including required related records when exporting records
* Support for partial local cache updates in GitLab store
* Support for parallel local cache creation in GitLab store
* Support for parallel exports in Records exporter
* GitLab store push returns resulting commit ID
* Copyright holders in licence tab
* Catalogue site verification
* e2e accessibility test for back to top link
* e2e responsive design test for primary navigation links
* Additional primary navigation items
* Exporter base class for resources (i.e. that process multiple records)
* Web Accessible Folders (WAF) exporter
* HTML meta tags for application and build information
* Scheduled verification of the production static site contents
* Deployment to BAS central workstations as a custom environment module

### Fixed

* Pre-commit config for Python type checking
* Fixing false positives when checking if records have changed in import task
* Logging in parallel tasks

### Changed

* Replacing public website search prototype to use WordPress REST API
* Paper map distribution option text updated to be less exclusive
* Record and Item test fixtures refactored into a more logical structure
* GitLab store push return type changed to a CommitResults class
* Minor fixes and improvements to dev tasks
* Config classes now support pickling
* Refactoring template rendering and HTML prettifying into base exporter utilities
* Refactoring catalogue item rendering into associated exporter for consistency
* Applying HTML prettifying to all rendered HTML outputs
* Refactoring proto-index into a regular page
* Refactoring PageMetadata into SiteMetadata with additional properties (commit, formatted build time)
* Refactoring exporters to use avoid using Config classes
* Refactoring item aliases exporter to generate HTML content using an element tree
* Refactoring record import task to separate out Zap ⚡️ editor specific processing

### Removed

* Reverting WordPress REST API based replacement of public website search prototype back to static JSON output

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
<!-- pyml enable no-duplicate-heading,no-duplicate-header -->
