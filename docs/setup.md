# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Setup

## Setup

## Terraform

Terraform is used for:

* resources required for protecting and accessing the *Repository* components
* resources required for hosting the *Catalogue* [static website](/docs/implementation.md#s3-static-website)
* resources required for hosting the Git repositories used for
  [CSW revision tracking](/docs/implementation-csw.md#csw-revision-tracking)

You will need access to these accounts to provision these resources:

* [BAS Terraform remote state project](#terraform-remote-state)
* [BAS AWS account 🔒](https://gitlab.data.bas.ac.uk/WSF/bas-aws)
* [BAS GitLab instance 🛡️](https://gitlab.data.bas.ac.uk/WSF/bas-gitlab)
* NERC Azure tenancy

```shell
$ cd support/terraform
$ docker compose run terraform

$ az login --allow-no-subscriptions

$ terraform init
$ terraform validate
$ terraform fmt
$ terraform apply

$ exit
$ docker compose down
```

**Note:** The `terraform apply` step will need to be taken in stages for Azure application registrations. See the notes
in `support/terraform/56-azure_app_registrations.tf` for details.

### Manual setup - Entra app registrations

Once provisioned, the following steps need to be taken manually to configure Entra app registrations:

1. set branding icons (if desired)
2. set [Entra permissions](#entra-permissions)
3. [assign roles](/docs/workflow-permissions-users.md) to users and/or groups
4. set `accessTokenAcceptedVersion: 2` in both application registration manifests

**Note:** Assignments are 1:1 between users/groups and roles but there can be multiple assignments. I.e. roles `Foo`
and `Bar` can be assigned to the same user/group by creating two role assignments.

### Manual setup - GitLab projects

Once provisioned, the following steps need to be taken manually to configure the GitLab projects used for CSW revision
tracking:

1. for the [Revision Tracking bot user 🔒](https://gitlab.data.bas.ac.uk/admin/users/bot-add-catalogue-records-tracking)
   in the GitLab Admin centre:
    * choose the *Confirm user* option to skip verifying the email address assigned to the user
    * choose the *Impersonate user* option
    * from the [Edit Profile 🔒](https://gitlab.data.bas.ac.uk/-/profile) page:
        * set the avatar to '/support/gitlab-avatars/revision-tracking.jpg'
        * set status to: '🤖 Bot User'
        * set pronouns to: 'They/Them'
        * set job title to: 'Records Tracking Bot'
        * set organisation to: 'British Antarctic Survey'
        * set biography to 'I am a bot used to track changes made to metadata records in the SCAR ADD Metadata Toolbox
          project.'
        * set private profile to *True*
    * from the [Access Tokens 🔒](https://gitlab.data.bas.ac.uk/-/profile/personal_access_tokens) page:
        * create a new Personal Access Token:
            * token name: 'scar-add-metadata-toolbox-internal'
            * expiry date: *None*
            * scopes: *write_repository*
        * save token in 1Password
    * from the [Notifications 🔒](https://gitlab.data.bas.ac.uk/-/profile/notifications) page:
        * set global notification level to: *Disabled*
2. for the Revision Tracking GitLab
   [Production 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-production) project:
    * under *Settings* -> *General*:
        * set *Avatar* to '/support/gitlab-avatars/revision-tracking.jpg'
        * under *Visibility*, disable all features except 'Repository'
        * (this will hide the 'Repository' sidebar section until an initial commit is made)
3. repeat the above steps for the
   [Integration 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-catalogue-records-integration) project, except:
    * set *Avatar* to '/support/gitlab-avatars/revision-tracking-inverted.jpg'

### Terraform remote state

State information for this project is stored remotely using a
[Backend](https://www.terraform.io/docs/backends/index.html).

Specifically the [AWS S3](https://www.terraform.io/docs/backends/types/s3.html) backend as part of the
[BAS Terraform Remote State 🛡️](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state) project.

Remote state storage will be automatically initialised when running `terraform init`. Any changes to remote state will
be automatically saved to the remote backend, there is no need to push or pull changes.

#### Remote state authentication

Permission to read and/or write remote state information for this project is restricted to authorised users. Contact
the [BAS Web & Applications Team](mailto:servicedesk@bas.ac.uk) to request access.

See the [BAS Terraform Remote State 🛡️](https://gitlab.data.bas.ac.uk/WSF/terraform-remote-state) project for how these
permissions to remote state are enforced.

## Entra permissions

[Terraform](#terraform) will create and configure the relevant Entra application registrations required for using
[OAuth](/docs/implementation.md#oauth) to protect the CSW catalogues.

Manual approval by a Tenancy Administrator (UKRI) is needed to grant the registration representing the *client* role
of the application access to the registration for the *server* role.

This has been approved by NERC RTS in
[MAGIC/add-metadata-toolbox#3 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/3).

## BAS IT

### Flask application setup

Add a new application to BAS IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible) project.

#### Postgres database

Manually request a new PostGIS database for the [CSW backing databases](/docs/implementation-csw.md#csw-backing-databases)
from the BAS IT ServiceDesk and run required [setup](#pycsw-backing-database-setup) when provisioned.

#### BAS General Load Balancer

Manually request entries are set up in the BAS General Load Balancer for:

1. Data Catalogue [static site](/docs/implementation.md#s3-static-website) URLs:
    * for both the production and testing URLs (`data.bas.ac.uk`, `data-testing.data.bas.ac.uk`):
    * the paths to request are the top-level directories within the static site (e.g. `/items/`)
    * the [Health Check](/docs/implementation.md#health-checks) can be used in HAProxy, providing the check frequency
      is lowered to 10 seconds
2. the [Downloads proxy](/docs/implementation-downloads-proxy.md) instance endpoints:
    * (see [MAGIC/add-metadata-toolbox#242 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/242)
      for an example)
    * **Note:** ensure HAProxy health checks are disabled for this service, as it will incur a cost

## BAS API Load Balancer

Manually [add a new service 🛡️](https://gitlab.data.bas.ac.uk/WSF/api-load-balancer#adding-a-new-service) and related
[documentation 🛡️](https://gitlab.data.bas.ac.uk/WSF/api-docs#adding-a-new-service-service-version) for the CSW, health
check and other server side endpoints. See
[MAGIC/add-metadata-toolbox#60 🛡️](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/issues/60) for an example.

## Nagios checks

Request URL checks are set up in the [PDC Nagios instance 🛡️](https://gitlab.data.bas.ac.uk/nagios/config/bslnagios) for:

* both [Health Check](/docs/implementation.md#health-checks) endpoints
* a CSW `GetCapabilities` request for the published catalogue

See [bas-nagios#52 🛡️](https://gitlab.data.bas.ac.uk/tdba/bas-nagios/-/issues/52) for an example request.

## PyCSW backing database setup

Backing databases for PyCSW servers require initialisation using the `csw setup db`
[CLI command](/docs/cli-reference.md#csw-setup-db) for both the *published* and *unpublished* repositories.

**Note:** Backing databases must use the Postgres engine with the PostGIS extension enabled.

Normally this command will create the required database table, geometry column and relevant indexes. As catalogues only
require a single table, multiple can be stored in the same database/schema. However, two of the indexes used
(`fts_gin_idx` [full text search] and `wkb_geometry_idx` [binary geometry]) are named non-uniquely, preventing multiple
catalogues being co-located in the same schema.

This appears to be an oversight, as all other indexes are made unique by prefixing them with the name of the records
table, and doing this manually for these indexes appears to work without issue. To work around this issue, you will need
to manually modify the indexes of catalogue tables once they've been set up.

Assuming the *Unpublished catalogue* is set up first, perform these steps *before* setting up the *Published catalogue*:

1. verify that the `records_unpublished` table was created successfully (contains `fts_gin_idx` and `wkb_geometry_idx`
   indexes)
2. alter the affected indexes in the `records_unpublished` table [1]
3. set up the *Published catalogue* `flask csw setup published`
4. alter the affected indexes in the second table [2]

[1]

```sql
ALTER INDEX fts_gin_idx RENAME TO ix_records_unpublished_fts_gin_indx;
ALTER INDEX wkb_geometry_idx RENAME TO ix_unpublished_wkb_geometry_idx;
```

[2]

```sql
ALTER INDEX fts_gin_idx RENAME TO ix_records_published_fts_gin_indx;
ALTER INDEX wkb_geometry_idx RENAME TO ix_published_wkb_geometry_idx;
```

## CSW revision tracking repository setup

Backing git repositories used for [CSW Revision Tracking](/docs/implementation-csw.md#csw-revision-tracking)
(where enabled), requires initialisation using the `csw setup repo`
[CLI command](/docs/cli-reference.md#csw-setup-repo) for the *unpublished* repository.

**Note:** Make sure to set the `CSW_SERVER_CONFIG_UNPUBLISHED_TRACKING_REMOTE_URL` environment variable on the client
side when running this command.
