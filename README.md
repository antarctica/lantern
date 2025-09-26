# Lantern

A prototype [Data Catalogue](https://data.bas.ac.uk/-/index) for BAS discovery metadata.

## Overview

The BAS Data Catalogue is a data discovery tool used to find, evaluate and access resources produced, managed and/or used
by the [British Antarctic Survey](https://www.bas.ac.uk) and [UK Polar Data Centre](https://www.bas.ac.uk/data/uk-pdc/).
This includes datasets, products (maps), services and other information.

<!-- pyml disable md028 -->
> [!IMPORTANT]
> This project is temporary to formalise and build out refactored components initially developed in the
> [BAS Assets Tracking Service](https://github.com/antarctica/assets-tracking-service) that will form the next release
> of the [ADD Metadata Toolbox 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox), which will form the new
> BAS Data Catalogue.

> [!NOTE]
> This project is focused on needs within the British Antarctic Survey. It has been open-sourced in case parts are of
> interest to others. Some resources, indicated with a '🛡' or '🔒' symbol, can only be accessed by BAS staff or
> project members respectively. Contact the [Project Maintainer](#project-maintainer) to request access.
<!-- pyml enable md028 -->

## Usage

See [Access](/docs/access.md) documentation for how to access catalogue records.

See [Usage](/docs/usage.md) documentation for how to load records and build the catalogue static site.

## Architecture

See [Architecture](/docs/architecture.md) documentation.

## Infrastructure

See [Infrastructure](/docs/infrastructure.md) documentation.

## Development

See [Development](/docs/dev.md) documentation.

## Releases

- [latest release 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp/-/releases/permalink/latest)
- [all releases 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp/-/releases)

### Release workflow

Create a
[release issue 🛡](https://gitlab.data.bas.ac.uk/MAGIC/lantern-exp/-/issues/new?issue[title]=x.x.x%20release&issuable_template=release)
and follow its instructions.

## Project maintainer

Mapping and Geographic Information Centre ([MAGIC](https://www.bas.ac.uk/teams/magic)), British Antarctic Survey
([BAS](https://www.bas.ac.uk)).

Project lead: [@felnne](https://www.bas.ac.uk/profile/felnne).

## Data protection

A Data Protection Impact Assessment (DPIA) is in place for this project, ref:
[4213 🔒](https://app-uk.onetrust.com/assessment/details/5ef15cb7-5736-446c-9a3c-c5d0d2751109).

## Licence

Copyright (c) 2024-2025 UK Research and Innovation (UKRI), British Antarctic Survey (BAS).

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
