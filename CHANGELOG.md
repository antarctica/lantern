# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Change log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Azure AD app registrations as Terraform resources
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)

### Changed

* Updating to Terraform 0.12.x, requiring syntax changes mainly for interpolation
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)
* Switching to a Terraform Docker image that includes the Azure CLI
  [#3](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues/3)

## [0.1.1] - 2020-06-02

### Fixed

* Amending `parse_version.py` packaging script to prevent pre-calculated version strings being broken if fed back in

## [0.1.0] - 2020-06-02

### Added

* Initial version [MAGIC/add#141](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/141)
