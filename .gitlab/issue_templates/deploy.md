/label ~"meta: deploy"
/relate #...

Follow on to #...

Tagged releases will be deployed to the IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible)
development environment automatically.

Once confirmed as working:

1. [x]  create a deployment issue
1. [ ]  create a branch in the IT [Ansible 🛡️](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/issues) project
1. [ ]  create a merge request for the branch, referencing this deployment issue in this project
1. [ ]  update the [`add_toolbox_version`](https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/group_vars/magic/add-metadata-toolbox.yml#L11) variable
1. [ ]  raise a BAS IT Service Desk request asking the server staging environment to be updated via Ansible [1]
1. [ ]  update the client staging environment via Ansible [2]
2. [ ]  when working, update the Service Desk request to update the server production environment via Ansible [3]
1. [ ]  update the client production environment via Ansible [4]
1. [ ]  when working, close the BAS IT Service Desk request and merge MR into the main branch of the IT Ansible project
1. [ ]  close milestone in this project

---

[1] Example service desk ticket (replace all `...` values, most are the links):

<blockquote>
Hi,

I would like to deploy a new version of the SCAR ADD Metadata Toolbox [1], version v... [2].

I have updated the Ansible config [3] and deployed to the development environment, which is working.

Please could someone trigger a deployment to staging.

Thanks,
Felix.

[1] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox

[2] https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/releases/v...

[3] https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/merge_requests/...
</blockquote>

[2]

As per https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/README.MAGIC.md#run-a-playbook:

```
$ invoke ansible -e staging magic/add-metadata-toolbox-client
```

[3] ...

[4]

As per https://gitlab.data.bas.ac.uk/station-data-management/ansible/-/blob/master/README.MAGIC.md#run-a-playbook:

```
$ invoke ansible -e production magic/add-metadata-toolbox-client
```
