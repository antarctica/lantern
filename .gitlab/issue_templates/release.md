<!-- SCAR ADD Metadata Toolbox release issue template -->

<!--
Set issue title to 'X.X.X release' e.g. '0.5.0 release'
-->

For all releases:

1. [x] create a release issue
2. [ ] create a merge request from release issue
3. [ ] close the release in `CHANGELOG.md`
4. [ ] bump Python package version `poetry version [minor/patch]`
5. [ ] push changes, merge the merge request into `main` and tag with version
6. [ ] create a new GitLab release, using the change log entry as release notes
7. [ ] link the GitLab release to the milestone and [Python package](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/packages)
8. [ ] close the GitLab milestone for the release
9. [ ] if needed, create a new milestone for the next release
