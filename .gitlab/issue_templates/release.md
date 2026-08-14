<!-- pyml disable-next-line md041 -->
/label ~"meta: release"

1. [x] create a release issue (title: 'x.x.x release', milestone: x.x.x)
1. [ ] create merge request from release issue
1. [ ] review [Documentation](/docs)
1. [ ] review the [OpenAPI definition](/docs/site.md#openapi-definition) and `x-scalar-stability` statements
1. [ ] review the [Change log](/CHANGELOG.md)
1. [ ] review the roadmap (`src/lantern/resources/templates/_views/guides/roadmap.html.j2`)
1. [ ] run the `release` [Development task](/docs/dev.md#development-tasks) with `major`/`minor`/`patch` as an argument
1. [ ] commit and push changes
1. [ ] merge into `main`
1. [ ] trigger staging Ansible deployment and complete required role
  [Cleanup Tasks 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/tree/master/roles/magic/lantern#post-deployment-reset)
1. [ ] delete any virtual environments created for pre-deployments (except the most recent)
1. [ ] tag merge commit with version prefixed with `v` (e.g. `v0.5.0`)
1. [ ] rebuild the live site to create content referencing new cache busting value (which is based on version)
