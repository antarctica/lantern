# Lantern - Architecture

## BAS Catalogue

`lantern.catalogue.BasCatalogue`

The BAS Catalogue underpins the BAS Data Catalogue as the only supported [Catalogue](#catalogues) and part of the
MAGIC [Spatial Data Infrastructure (SDI)](https://github.com/antarctica/magic-sdi).

> [!TIP]
> See the [Access](/docs/access.md) docs for how to access the BAS Catalogue.

At a high level it consists of these components:

![BAS Catalogue overview](/docs/img/architecture-bas-overview.png)

- a BAS multi-store [Repository](#repositories) to read and write records in:
  - a [GitLab](#gitlab) store as a source of truth for Records and their revisions
  - an [Algolia](#algolia) store for [Search](/docs/site.md#search) indexing
- an experimental editor, [Zap ⚡️](https://github.com/felnne/zap) to create Records manually
- automated systems maintaining their own Records
- sub-catalogues for:
  - testing and live environments (used for previewing content and general access respectively)
  - trusted and untrusted content, per environment
- for untrusted (public) content, a [Site](#sites) hosted in [AWS S3](#amazon-s3) for public consumption
- for trusted (internal) content, a [Site](#sites) hosted in the
  [BAS Operations Data Store 🛡](https://gitlab.data.bas.ac.uk/MAGIC/ops-data-store), restricted to the *Admin* role

> [!NOTE]
> Trusted content and [Publishing](#trusted-publishing) is used for items containing decrypted
> [Administration Metadata](/docs/models.md#item-administrative-metadata) which are considered sensitive.

See these additional diagrams for:

- how these components are used for [Creating and Updating Records](/docs/img/architecture-bas-editing.png)
- how these components are used for [Publishing](/docs/img/architecture-bas-publishing.png) content

The BAS Catalogue Repository:

- reads and writes Records as [Record Revisions](/docs/models.md#record-revisions) in GitLab:
  - supports branches and merge requests, with methods to open, list and merge changesets of Records
  - always reads the latest revision of each Record for a given branch
  - always merges changesets into the default branch
- writes Records to Algolia in a global search indexing:
  - using a single, global, all Records index tracking the default GitLab branch
- coordinates stores to ensure consistency wherever possible:
  - by updating records in Algolia when a GitLab branch is merged into the default branch
- does not support renaming or removing Records

## Trusted Publishing

The `trusted` [Export Metadata](/docs/models.md#export-metadata) flag can be used to indicate where static site content
is considered sensitive, and MUST be only be available to a restricted audience. This is termed trusted publishing.

Where set, [Outputs](#outputs) MAY include [Administrative Metadata](/docs/models.md#item-administrative-metadata) for
example.

## Application

`lantern`

A Python application defined within the `src/lantern` package consisting of:

- a logging class, including [Sentry](/docs/monitoring.md#sentry) integration
- a [Config](/docs/config.md) class
- a [Catalogue](#catalogues) class

## Catalogues

`lantern.catalogues`

Catalogues are the core component of this project, responsible for:

- managing [Records](/docs/models.md#records)
- transforming these into a static website for discovery
- [Checking](/docs/monitoring.md#site-checks) the static website's content and downloads linked from records

A minimum Catalogue consists of:

![Minimum catalogue components](/docs/img/architecture-generic-min.png)

- a [Store](#stores) to manage and access Records created by [Editors](#record-editors)
- a [Site](#sites) generator
- an [Exporter](#exporters) to publish the generated site to a hosting service, such as [AWS S3](#amazon-s3)
- a [Checker](/docs/monitoring.md#site-checks) to verify generated site content and downloads linked from records

> [!IMPORTANT]
> Only the [BAS Catalogue](#bas-catalogue) is officially supported by this project.

## Repositories

`lantern.repositories`

Repositories abstract managing [Records](/docs/models.md#records) in one or more [Stores](#stores) within larger
[Catalogues](#catalogues).

## Sites

`lantern.site.Site`

Sites are static websites built from a set of Records and other content as the output of a [Catalogue](#catalogues).

They generate content, checks and/or cache invalidation keys for content from [Outputs](#outputs) using a
[Store](#stores) to access records.

> [!TIP]
> A static site is used over a dynamic site for its robustness and ease of hosting, such as via [AWS S3](#amazon-s3).

See the [Outputs](/docs/outputs.md) docs for information about the content within a site.

See the [Static site](/docs/site.md) docs for information about the site structure, templates, styles, scripts, etc.

See the [Checks](/docs/monitoring.md#site-checks) docs for information about the checks generated for a site.

## Stores

`lantern.stores`

Stores create, update, read and delete Records in local or remote systems, such as GitLab. They are used in
[Repositories](#repositories) in larger [Catalogues](#catalogues).

They provide access to Records used to build a [Site](#sites) and may add or update Records for use in future builds.

See the [Stores](/docs/stores.md) docs for more information.

## Outputs

`lantern.outputs`

Outputs create different parts of a [Site](#sites), such as Item pages, general resources such as CSS files and
monitoring / API discovery endpoints. Outputs also create [Checks](/docs/monitoring.md#site-checks) for their content.

See the [Outputs](/docs/outputs.md) docs for more information.

## Exporters

`lantern.exporters`

Exporters save files to local or remote systems, such as an S3 bucket.

They are used in [Sites](/docs/architecture.md#sites) to store and/or publish content generated by
[Outputs](/docs/architecture.md#outputs).

See the [Exporters](/docs/exporters.md) docs for more information.

## Record editors

Editors create and update Record configurations. They may be interactive (for use by humans to author bespoke Records),
or automated systems, managing sets of Records for a particular purpose. All editors are treated equally.

In either case, Record configurations are loaded into the Catalogue and then persisted via a [Store](#stores).

See the [Usage](/docs/usage.md) docs for information about creating and updating Records.

## GitLab

The [BAS GitLab instance](https://gitlab.data.bas.ac.uk) is used as a remote Records [Store](#stores) and change
tracking tool.

GitLab is used for:

- consistency with other projects (including this project)
- support for merge requests for simple record review workflows via a hosted user interface
- being able to manage provisioning, permissions and git operations programmatically

See the [GitLab Store](/docs/stores.md#gitlab-store) for details on how Records are stored in GitLab.

See the [Infrastructure](/docs/infrastructure.md#gitlab) docs for more information about the GitLab project used.

## Amazon S3

Amazon Web Services (AWS) [Simple Storage System (S3)](https://aws.amazon.com/s3/) static hosting and a
[CloudFront Distribution](https://aws.amazon.com/cloudfront/) are used to host untrusted [Site](#sites) content.

AWS is used for:

- its high availability, global infrastructure and low cost
- its support for object level server redirects and content metadata
- the ability to manage provisioning, access control and content programmatically

See the [S3 Exporter](/docs/exporters.md#s3-exporter) for details on *how* information is stored in S3.

See the [Static Site](/docs/site.md) docs for more information on *what* is stored in S3.

> [!NOTE]
> AWS CloudFront caches content in the live site environment by default. The BAS Catalogue automatically invalidates
> content as needed when publishing.

## Algolia

[Algolia](https://www.algolia.com) is used as a remote Records [Store](#stores) specifically for enabling
[Site Search](/docs/site.md#search) functionality.

Algolia is used for:

- its focus on search, speed and generous free tier
- frontend library to implement a search interface
- ease of managing the backend index

See the [Algolia Item Model](/docs/models.md#algolia-search-items) for details on *what* is indexed for each Record.

See the [Algolia Store](/docs/stores.md#algolia-store) for details on *how* Records are stored in Algolia.

## ArcGIS Online

[ArcGIS Online](https://www.arcgis.com) is used in Records as a key data access system for spatial services. It also
underpins the Embedded Maps Service used for [Item Extent Visualisations](/docs/site.md#item-extent-maps) functionality.

ArcGIS Online is used for:

- consistency with other projects and to align with the BAS Spatial Data Infrastructure
- its stability, performance and features

## Infrastructure

See the [Infrastructure](/docs/infrastructure.md) docs for more information about the underlying infrastructure used.

> [!NOTE]
> Managed services, external to BAS on-premise infrastructure, are generally preferred where practical and available
> for stability, performance and agility as the project grows.
