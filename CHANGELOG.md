# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Documentation on database sync between staging and production databases for testing
  [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44)
* API usage documentation 
  [#60](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60)
* Adding IT setup/deployment instructions 
  [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44)

### Fixed

* Reference to S3 bucket environment variable in config class
  [#113](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/113)
* `site copy-assets` command compatibility with Python 3.6 to delete files recursively
  [#112](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/112)
* Removing unavailable/misleading configuration options from Podman environment file template
  [#111](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/111)
* HTTP exceptions in CSW client calls were not correctly re-raised for error handling
  [#110](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/110)
* Fixing Black code formatting
  [#109](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/109)
* Adding missing label for outdated items in item template
  [#107](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/107)
* Incorrect name of CLI in command reference documentation
  [#103](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/103)
* Using `release` instead of `review` images reference in Podman wrapper script
  [#76](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/76)
* Enabling Sentry in production environments
  [#74](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/74)

### Changed

* Using `api.bas.ac.uk` endpoints in Podman environment configuration
  [#60](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60)

## [0.2.3] - 2020-09-15

### Fixed

* Removing hardcoded location for static site assets
  [#97](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/97)

## [0.2.2] - 2020-09-14

### Fixed

* Collections file is no longer inadvertently modified on class initialisation
  [#95](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/95)
  
### Changed

* Working around absolute dates in test records 'expiring' and giving different test results (needs permanent fix)
  [#96](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/96)
 
## [0.2.1] - 2020-08-26

### Fixed

* PyCSW patching (incorrectly targeted Python 3.8 rather 3.6)
  [#72](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/72)

## [0.2.0] - 2020-08-26

### Changed [BREAKING!]

* Updating application configuration options, including reducing the options that can be set at runtime
  [#14](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/14)
* Removing entrypoint/`manage.py` in favour of `FLASK_APP` environment variable
  [#47](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/47)

### Added

* Support for multiple collections
  [#53](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/53)
* The order of items in collections can be defined
  [#65](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/65)
* Records and collections can now be managed in bulk, rather than individually (e.g. export all records at once)
  [#52](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/52)
  [#49](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/49)
* Improved data licence summary for CC 4.0 (warranties and disclaimers)
  [#24](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/24)
* Markdown can now be used for item titles, abstracts and lineage statements
  [#55](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/55)
* WMS instructions panel is now highlighted when opened
  [#41](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/41)
* User conformation added when publishing the static site
  [#43](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/43)
* BAS Nagios instance trusted to use CSW catalogues for monitoring
  [#70](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/70)
* Support for setting the logging level at runtime
  [#25](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/25)
* Lists of information shown using tables in CLI commands
  [#23](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/23)
* Documentation guides for adding/updating collections/records and assigning application permissions
  [#33](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/33)
* Docker image tag expiration policy
  [#12](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/12)
* Review apps using Nomad
  [#11](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/11)
* Additional developer documentation
  [#8](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/8)
* Support for Markdown in feedback and item contact forms
  [#7](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/7)
* Azure AD app registrations as Terraform resources
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)

### Fixed

* Incorrect environment variable reference for CSW endpoints
  [#5](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/5)
* Documenting workaround for initialising PyCSW tables
  [#6](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/6)

### Changed

* Fundamental application refactoring, creating new `classes`, `commands`, `csw` and `hazmat` modules
  [#15](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/15)
* Publishing application packages via PyPi
  [#71](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/71)
* Updating project documentation inc. CLI reference
  [#33](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/33)
* Various PyCharm configuration changes (run/debug configurations etc.)
  [#15](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/15)
* Switching to refactored/externalised Python version parsing script
  [#12](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/12)
* Improvements to Continuous Integration/Deployment pipeline
  [#12](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/12)
* Updating Python dependencies via Poetry
  [#9](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/9)
* Downgrading to Python 3.6 for compatibility with BAS IT
  [#72](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/72)
* Poetry update removed from Dockerfile and made a manual action
  [#9](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/9)
* Updating to Terraform 0.12.x, requiring syntax changes mainly for interpolation
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)
* Switching to a Terraform Docker image that includes the Azure CLI
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)
* Switching to NERC tenancy for OAuth authentication/authorisation
  [#4](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/4)

## [0.1.1] - 2020-06-02

### Fixed

* Amending `parse_version.py` packaging script to prevent pre-calculated version strings being broken if fed back in

## [0.1.0] - 2020-06-02

### Added

* Initial version [MAGIC/add#141](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/141)
