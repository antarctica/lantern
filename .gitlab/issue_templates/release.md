<!-- pyml disable-next-line md041 -->
/label ~"meta: release"

1. [x] create a release issue (title: 'x.x.x release', milestone: x.x.x)
1. [ ] create merge request from release issue
1. [ ] review [Documentation](/docs)
1. [ ] review the [OpenAPI definition](/docs/site.md#openapi-definition) and `x-scalar-stability` statements
1. [ ] review [Change log](/CHANGELOG.md)
1. [ ] run the `release` [Development task](/docs/dev.md#development-tasks) with `major`/`minor`/`patch` as an argument
1. [ ] commit and push changes
1. [ ] merge into `main` and tag merge commit with version prefixed with `v` (e.g. `v0.5.0`)
1. [ ] [Reset]https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/roles/lantern/README.md#post-deployment-reset
       resources created during deployment
1. [ ] if needed, delete any un-used virtual environments created for pre-deployments (except the most recent)
