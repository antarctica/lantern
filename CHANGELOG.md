# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed [BREAKING!]

* Static health check endpoint removed (see new dynamic endpoint for an alternative)
  [#282](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/282)

### Changed [BREAKING!]

* Minimum Python version increased to 3.8.1
  [#289](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/294)
* Minimum Poetry version increased to 1.2.x
  [#312](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/312)

### Added

* 404 error handler route for server side endpoints
  [#319](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/319)
* Dynamic health endpoint indicating basic liveliness and installed package version
  [#282](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/282)
* Flake8 `pyproject.toml` support via `flake8-pyproject`
  [#300](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/300)
* Flake8 comprehensions plugin
  [#259](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/259)
* Flake8 Pep8 naming plugin
  [#260](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/260)
* Documentation on updating minimum Python version
  [#289](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/294)

### Fixed

* Correcting incorrect types on generator functions
  [#316](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/316)
* Suppressing currently unsupported ESRI Living Atlas distribution options from displaying in a broken state
  [#294](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/294)
* Incorrectly committed pyenv `.python-version` file
  [#306](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/306)
* GeoPackage media type in README examples
  [#307](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/307)
* Correcting hostname for staging server CSW endpoints in README instructions
  [#308](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/308)
* Correcting git command in IT deployment README instructions
  [#309](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/309)

### Changed

* Refactoring how CSW requests are evaluated with respect to permission checks
  [#73](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/73)
* Improving documentation
  [#315](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/315)
* Migrating additional PyCSW workarounds to Hazmat module
  [#270](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/270)
* Upgrading project dependencies
  [#289](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/289)
* Improving release issue template
  [#310](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/310)
* Improving doc blocks, code formatting, typos, minor syntax changes and PyCharm inspections
  [#311](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/311)
* Improving Downloads Proxy documentation
  [#293](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/293)

### Removed

* Invalid missing CSW catalogue test which was was not being handled by the expected function and therefore misleading
  [#318](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/318)
* Paw API document (migrated to Paw cloud)
  [#313](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/313)

## [0.5.0] - 2022-10-10

### Changed [BREAKING!]

* Migrating to BAS Metadata Library ISO 19115 V3 record configurations
  [#267](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/267)
* Refactoring Collections to use Records, rather than a standalone implementation
  [#171](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/171)
* Switching to new GCMD keywords URL
  [#236](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/236)

### Added

* Support for multiple geographic and temporal extents
  [#249](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/249)
* Support for records with a 'not planned' resource maintenance frequency
  [#182](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/182)
* Updating to BAS Metadata Library 0.9.1
  [#251](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/272)
* Updating to BAS Metadata Library 0.9.0
  [#251](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/251)
* Additional documentation on how to run BAS IT Ansible playbooks for development deployments
  [#213](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/213)
* Additional documentation on how log rotate is used in BAS IT deployments
  [#215](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/215)
* Additional documentation for resetting the Downloads Proxy staging environment
  [#248](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/248)
* Downloads Proxy version 2
  [#242](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/242)
* Note about data currency in WMS usage instructions
  [#233](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/233)

### Fixed

* Updating Poetry install method and location in CI/CD image
  [#269](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/269)
* ensuring any pre-existing auth file is removed when testing sign-out command where an auth file does not yet exist
  [#231](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/231)
* removing experimental watermark style accidentally applied to all catalogue pages
  [#234](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/234)
* documentation inaccuracies and tweaks
  [#232](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/232)
* reducing ambiguity of site build all command
  [#225](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/225)
* ensuring test coverage is always captured in CI
  [#210](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/210)

### Changed

* Updating the URL used to detect Shapefile downloads to IANA value
  [#275](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/275)
* Updating project dependencies
  [#268](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/268)
* Updating Safety linting command in CI
  [#273](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/273)
* Replacing extent map with ESRI ArcGIS JS client and map data
  [#42](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/42)
* Suppressing CSW dependency warnings
  [#224](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/224)
* Upgrading Terraform configuration to 1.0.0
  [#241](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/241)

## [0.4.3] - 2022-03-08

### Changed

* Increasing minimum SQL Alchemy version in requirements file
  [#207](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/207)

### Removed

* Old code used for checking CSW backing database tables exist
  [#208](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/208)

## [0.4.2] - 2022-02-16

### Fixed

* Release process from 0.4.1 release
  [#206](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/206)

## [0.4.1] - 2022-02-16

### Fixed

* Dynamic imports used in vendored PyCSW/OWSlib dependency
  [#204](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/204)

## [0.4.0] - 2022-01-24 [BREAKING!]

### Changed [BREAKING!]

* Relicensing project under the MIT licence (from the UK Open Government Licence)
  [#188](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/187)

### Added

* Upgraded project dependencies
  [#188](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/188)
* Upgraded to BAS Metadata Library v0.8.0
  [#183](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/183)
* Vendored PyCSW and OWSlib dependencies
  [#193](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/193)
* Flake8 linting
  [#198](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/198)
* Publishing packages to GitLab package registry
  [#203](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/203)

### Fixed

* Items incorrectly required a Spatial Reference System to be set when exporting as records
  [#157](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/157)
* URLs for NVS vocabularies which were set incorrectly in records
  [#175](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/175)
* Test failures related to dependency changes and paths to test resources
  [#197](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/197)
* Test warnings related to deprecated `importlib_resources` methods
  [#199](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/199)

### Changed

* Simplifying and CI/CD workflow
  [#189](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/189)
  [#196](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/196)
* Vendoring PyCSW and OWSlib dependencies within Hazmat module
  [#193](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/193)
* Restructuring package to use `src` directory
  [#195](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/195)
* Switching to Poetry based development environment
  [#195](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/195)

### Removed

* Record seeding support (in favour of importing existing records)
  [#128](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/128)
* Podman and Nomad deployment options
  [#202](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/202)

## [0.3.0] - 2021-07-02

### Added

* Support for PNG, JPEG and PDF transfer option formats
  [#155](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/155)
* Support for Open Government Licence (OGL)
  [#151](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/151)
* Markdown support for item citations
  [#153](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/153)
* Minimal support for product records
  [#156](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/127)
* Alert that JavaScript is required in item pages to enable tabs to work
  [#127](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/127)
* Python dependencies updated, inc. PyCSW to 2.6.0
  [#130](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/130)
* Poetry updated to 1.1.0
  [#131](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/131)

### Fixed

* Reference to item ID in item JS script
  [#162](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/162)
* Items using an invalid item bounding box geometry
  [#154](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/154)
* Items incorrectly used 3031 projection for all bounding boxes
  [#161](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/161)
* Items incorrectly required a revision date to be set in records
  [#118](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/118)
* Items incorrectly required a Spatial Reference System to be set in records
  [#157](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/157)
* Items incorrectly required a collection to be set in records
  [#119](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/119)
* Items incorrectly required transfer options to be set in records
  [#120](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/120)
* Items incorrectly required a lineage to be set in records
  [#135](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/135)
* Invalid contact/feedback form submissions when JavaScript is not used for form submission
  [#123](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/123)
* Incorrect use of temporal extent start from record as both temporal extent start and end in item class
  [#129](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/129)
* Missing PostGIS extension will trigger an exception when setting up a CSW catalogue
  [#132](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/132)
* Broken dependencies in newer Alpine image
  [#158](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/158)

### Changed

* Extent map is only shown when the extent tab is selected for an item
  [#164](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/164)
* Updating copyright year
  [#163](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/163)
* README improvements
  [#163](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/163)

### Removed

* Publisher from item and collection page templates, as this would always be the same value
  [#125](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/125)

## [0.2.4] - 2020-12-04

### Added

* Documentation on database sync between staging and production databases for testing
  [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44)
* API usage documentation
  [#60](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60)
* Adding IT setup/deployment instructions
  [#44](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/44)

### Fixed

* Missing sub-antarctic bounding geometry
  [#114](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/114)
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
