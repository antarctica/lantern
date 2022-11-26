<!-- SCAR ADD Metadata Toolbox deployment issue template -->

<!--
Set issue title to 'X.X.X deployment' e.g. '0.5.0 deployment'
-->

For all deployments:

1. [x]  create a deployment issue
1. [ ]  follow the [Deployment workflow](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/README.md#user-content-deployment-process) to deploy to IT development instance
1. [ ]  create Service Desk ticket to deploy the new release to the IT staging instance
1. [ ]  if successful, ask IT to merge deployment workflow MR and deploy new release to IT production
1. [ ]  re-deploy API documentation if needed <!-- 1. ~~re-deploy API documentation if needed~~ (not needed) -->
1. [ ]  close Service Desk ticket, and this issue, once deployed

<!-- If API documentation does not need re-deploying, replace with commented out alternative -->

---

Example service desk ticket (replace all [UPPER CASE] values, most are the links):

<blockquote>
Hi,
 
I would like to deploy a new version of the SCAR ADD Metadata Toolbox [1], version v[VERSION] [2].

This is deployed using the Ansible scripts in [3]. I think I have updated these correctly in [4] but I can't run them.

Could someone please review and deploy these changes as needed.

For reference, ticket #[PREVIOUS SERVICE DESK TICKET] describes the deployment of the previous release.

Thanks,
Felix.
 
[1] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox
 
[2] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/releases/v[VERSION]
 
[3] https://gitlab.data.bas.ac.uk/station-data-management/ansible
 
[4] https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/merge_requests/[MERGE REQUEST]
</blockquote>
