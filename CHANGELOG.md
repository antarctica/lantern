# Lantern - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Wherever possible, a reference to an issue in the project issue tracker should be included to give additional context.

<!-- pyml disable no-duplicate-heading,no-duplicate-header -->
## [Unreleased]

### Changed [!BREAKING]

* `ItemBase.abstract*` methods changed to `ItemBase.description*` (impacts externally maintained item subclasses)

### Added

* Development task for minimally cloning a record
* Development task for minimally initialising a GitLab records cache
* Support for configuring the GitLab store branch name
* Support for branch-based changesets in interactive publishing workflow
* Support for v2 MAGIC discovery profile
* Support for initiative records as 'project' items
* Support for container and resource 'super types' to more flexibly support similar item types
* Support for SAN based distribution options (skipped during verification)
* Support for running GitLab instance locally in development environments
* Additional validation for MAGIC Discovery profile Req. 06 (released date presence)
* Setup documentation for Plausible
* Store frozen (read-only) mode for publishing workflows
* 'js' development task for assembling JavaScript scripts
* OpenAPI definition and Scalar based interactive documentation for static site
* Reverse engineered JSON schema for site verification report data (for use in OpenAPI definition)
* Reverse engineered JSON schema for public website search items data (for use in OpenAPI definition)
* Supplemental icon audit and development task
* Icon added to back to top footer link
* Pickling support for administrative metadata keys
* Pickling support for GitLab store cache
* Static health check endpoint
* Sized support for stores to get number of records a store contains
* Additional footer navigation links
* 'admin-record' development task for viewing administrative metadata for a record
* custom Sentry user feedback widget
* Infrastructure as Code using OpenTofu

### Fixed

* Correcting dates in legal policy change logs
* Records repository bootstrap development task includes missing XML record files
* Disabling lineage statement in container item types
* Missing datestamp update in the clone record development task
* Correcting names for `STORE_GITLAB_CACHE_PATH`, `STORE_GITLAB_ENDPOINT` and `STORE_GITLAB_PROJECT_ID` config options
* Missing Open Graph and Schema.org metadata for static site pages
* Read-only database error when purging a GitLab local cache due to a stale connection

### Changed

* Upgrading to BAS Embedded Maps Service v0.3.0 with BAS Style Kit v1 theme
* Upgrading to latest linting and UV versions
* Supporting command line arguments in selecting records development task
* Supporting additional identifier formats in selecting records development task
* Refactoring record related development tasks to use common functions via (`tasks._record_utils` module)
* Refactoring and improving interactive publishing workflow
* Switching to dedicated GitLab bot user for GitLab Store and record publishing workflow (to post comments across projects)
* Including GitLab endpoint/instance in determining GitLab local cache validity (in addition to branch/ref)
* Splitting GitLab store and local cache into separate modules and stores (`GitLabStore` and `GitLabCachedStore`)
* Simplifying Store's to remove local subsets and `populate()` methods
* Using SQLite for GitLab store local cache for flexibility and performance
* Improving, simplified and streamlining exporters
* Using typing protocols for Store select methods to avoid duplicate inline type definitions
* Reorganising exporter utility methods
* Refactoring inline JavaScript in templates into standalone files
* Refactored CSS build process consistency with new 'js' process, inc. renaming 'tailwind' development task to 'css'
* Extracted Open Graph and Schema.org link preview metadata logic out of catalogue items into site data classes
* Minor page performance improvements
* Splitting 'base' layout into 'base' and 'main' layouts to allow full-width content
* Refactored HTML redirect page generation into utils module for sharing across exporters
* Switching to Font Awesome 7 hosted kit
* Refactored OGL symbol into a custom Font Awesome icon
* Refactored records exporter to prevent un/re-loading admin metadata keys and creating new stores per parallel worker
* Improving development tasks
* Replaced native Sentry user feedback widget with custom implementation for better consistency
* Vendored Sentry SDK to minimise external dependencies
* Recreating static site infrastructure within this project to use AWS static site Terraform module

### Removed

* Records load development task

## [0.4.0] - 2025-10-24

### Added

* Non-interactive record publishing workflow for integrating with other projects hosted on the central workstations
* Dark mode variant of item summary default thumbnail
* Support for CSV, FPL, GPX and MBTile file distribution options
* Support for custom labels and optional descriptions in distribution options
* Bot protection for item enquiry forms
* Infrastructure diagram and hosting information
* Initial administrative metadata support (GitLab issues and initial access permissions)
* Record utility methods for key values in supplemental information
* Item cross-reference record preset
* Initial admin tab for administrative metadata
* Development task for setting administrative metadata access permissions in records
* Support for MAGIC Products internal use licence

### Fixed

* Refactoring `ItemBase` to work with Records or Record Revisions (previously required RecordRevision's)
* Invalidating cache where a significant number of commits have occurred since the last update
* Preventing licences unknown to catalogue items breaking exports
* Item thumbnail alt text not describing content by associating with abstract via `aria-details`
* Minimum padding for all device sizes where auto centering would give zero margin
* Privacy policy page title

### Changed

* Documentation improvements
* Contextualising items fragment in item summaries for physical map products (sides rather than items)
* Increasing Catalogue specific record requirements to ensure file identifiers are UUIDs
* Catalogue items use binary restricted access control, defaulting to restricted
* Moving dict/list cleaning utils into new records utils package
* Improving distribution record presets
* Updating accessibility statement

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
