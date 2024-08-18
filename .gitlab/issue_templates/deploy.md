/label ~"meta: deploy"
/relate #[release issue]

Follow on to #[release issue].

1. [x]  create a deployment issue
1. [ ]  create a branch in the IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/issues) project
1. [ ]  create a merge request for this branch, referencing the deployment issue in this project
1. [ ]  deploy to the BAS IT Ansible [development environment](/docs/deploy.md#deploy-to-development-environment)
1. [ ]  when working, raise a BAS IT Service Desk request to deploy to the BAS IT Ansible staging environment [1]
1. [ ]  when working, update the BAS IT Service Desk request to deploy to the BAS IT Ansible production environment
1. [ ]  when working, close the BAS IT Service Desk request and merge MR into the main branch of the IT Ansible project
1. [ ]  close milestone in this project

---

[1] Example service desk ticket (replace all [UPPER CASE] values, most are the links):

<blockquote>
Hi,

I would like to deploy a new version of the SCAR ADD Metadata Toolbox [1], version v[VERSION] [2].

I have updated the Ansible config [3] and deployed to the development environment, which is working.

Please could someone trigger a deployment to staging.

Thanks,
Felix.

[1] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox

[2] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/releases/v[VERSION]

[3] https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/merge_requests/[MERGE REQUEST]
</blockquote>
