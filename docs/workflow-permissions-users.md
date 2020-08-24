# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Assigning permissions to users and groups

Follow this workflow to allow new users, or groups of users, to manage metadata records and/or publishing.

**Note:** You will need to be an ADD project staff member to perform these steps.

## Overview

Microsoft Azure Active Directory (AAD) is used for identity management and permissions management. 

ADD generally is managed by NERC/UKRI IT and ensure all BAS/NERC staff have a user account for example. They can also
create and maintain groups of users for ease of management (e.g. there is a group for all MAGIC team members).

This application defines a set of roles that can be assigned to users and/or groups to allow people to perform different
actions. These permissions can be assigned by an application owner (ADD project staff) using the Azure online portal.

Roles that can be assigned are:

* `BAS.MAGIC.ADD.Records.ReadWrite.All` - allows a user to create, retrieve, update and delete metadata records
* `BAS.MAGIC.ADD.Records.Publish.All` - allows a user to publish or retract metadata records

The `Records.ReadWrite.All` role is an essentially an *author* role and the `Records.Publish.All` an *editor* role.

By default:

* the `BAS.MAGIC.ADD.Records.ReadWrite.All` (author) role is assigned to all MAGIC team members (via the 
  [MAGIC security group (internal)](https://gitlab.data.bas.ac.uk/MAGIC/general/-/wikis/Azure-authentication#magic-security-group)).
* the `BAS.MAGIC.ADD.Records.Publish.All` (editor) role is assigned to ADD data managers

If additional users should be granted either or both role, follow these steps.

## Steps

1. login to the relevant part of the 
   [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ManagedAppMenuBlade/Users/objectId/8bfe65d3-9509-4b0a-acd2-8ce8cdc0c01e/appId/8b45581e-1b2e-4b8c-b667-e5a1360b6906)
2. click *Add user*
    * select the relevant user or group
    * select the relevant role
    * click *Assign*
    
**Note:** Only role can be assigned at a time, you can assign multiple roles by adding the same user again with the 
other role(s).
