# SCAR Antarctic Digital Database (ADD) Metadata Toolbox

Repository and Catalogue for
[SCAR Antarctic Digital Database (ADD) discovery metadata](http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/).

## Overview

At a high level, this project is made up of a:

1. Repository: for storing metadata records, acting as a source of truth
2. Catalogue: for displaying metadata records, acting as a discovery tool

These components map to components 4 and 6 in the draft ADD data workflow from
[MAGIC/add#139 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add/issues/139).

**Note:** This project is focused on needs within the British Antarctic Survey. It has been open-sourced in case parts
are of interest to others. Some resources, indicated with a '🛡' or '🔒' symbol, can only be accessed by BAS staff or
project members respectively. Contact the [Project Maintainer](#project-maintainer) to request access.

### Status

This project is a mature alpha.

This means core, required, components have been implemented but are subject to considerable change and refactoring.

Between releases major parts of this project may be replaced/rewritten. As major non-core features are yet to be
implemented, the shape and scope of this project may change significantly.

In time, this project will grow to cover other MAGIC datasets, products and activities. It may also be used as the seed
for a new BAS wide Data Catalogue.

Further information on upcoming changes to this project can be found in the issues and milestones in
[GitLab 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/issues).

### Purpose

A tool for ADD project members to:

* add, retrieve, update and delete metadata records about ADD datasets, where records are either:
  * published (accessible by anyone)
  * unpublished (accessible only by ADD project members, whilst in draft etc.)
* organise datasets into one or more collections
* publish metadata records when ready
* retract published metadata records if needed

Once published, records can be viewed through the *Catalogue* component, which provides:

- a static website, presenting published records as human-readable item and collection pages

This Catalogue is embedded within the current/legacy BAS Data Catalogue, the
[Discovery Metadata System (DMS) 🛡️](https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/discovery-metadata-system-external),
which is in the process of being replaced by a future version of this project.

## Usage

### Workflows

* [adding new records](docs/workflow-adding-records.md)
* [updating existing records](docs/workflow-updating-records.md)

### Available commands

[Command line reference](docs/cli-reference)

### Registering download proxy items

See the [Downloads Proxy](/docs/implementation-downloads-proxy.md#registering-downloads-proxy-artefacts-lookup-items)
documentation.

## Implementation

See [Implementation](/docs/implementation.md) documentation.

## Setup

See [Setup](/docs/setup.md) documentation.

## Development

See [Development](/docs/dev.md) documentation.

## Releases

- [latest release 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/releases/permalink/latest)
- [all releases 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/releases)

### Release workflow

Create a [release issue](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/new?issue[title]=x.x.x%20release&issuable_template=release)
and follow the instructions.

GitLab CI/CD will automatically create a GitLab Release based on the tag, including:

- milestone link
- change log extract
- package artefact
- link to README at the relevant tag

Releases then need to be [Deployed](#deployment) manually.

## Deployment

See [Deployment](/docs/deploy.md) documentation.

## Project maintainer

British Antarctic Survey ([BAS](https://www.bas.ac.uk)) Mapping and Geographic Information Centre
([MAGIC](https://www.bas.ac.uk/teams/magic)). Contact [magic@bas.ac.uk](mailto:magic@bas.ac.uk).

The project lead is [@felnne](https://www.bas.ac.uk/profile/felnne).

## License

Copyright (c) 2020-2024 UK Research and Innovation (UKRI), British Antarctic Survey (BAS).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
