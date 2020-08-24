# SCAR Antarctic Digital Database (ADD) Metadata Toolbox - Application command reference

## General information

### Running commands

When using the BAS central workstations as the `geoweb` user use:

```
add-metadata-toolbox [command]
```

E.g.:

```
add-metadata-toolbox version
```

Otherwise run commands using:

```
flask [command]
```

### Listing commands

All application commands can be listed by running the `add-metadata-toolbox` or `flask` without a command, or by adding 
the `--help` option (`add-metadata-toolbox --help` or `flask --help`).

This will list all top level commands or command groups. Commands within a group can be listed by calling the group as
a command (and optionally `--help` option), e.g. `add-metadata-toolbox records --help` or `flask records --help`.

### Command help

A brief description of each command and its options can be listed using the `--help` option, e.g. 
`add-metadata-toolbox records import --help` or `flask records import --help`.

### Bulk commands

Many commands have 'bulk' counterparts that can be used for convenience. Bulk commands internally call the non-bulk
version in a loop, and so work the same way as if you manually used the non-bulk command multiple times.

For example, the `records import` imports a single record from a file, whereas the `records bulk-import` command imports 
records from all files in a directory by internally calling `records import` on each file in the directory.

Bulk commands will stop at the first error they encounter, meaning if 20 records are imported and the 2nd causes an 
error for example, the remaining 18 records won't be imported because the 2nd record failed.

### Command permissions

Many commands can only be used by specific individuals or groups of individuals, typically either members of MAGIC or
data managers within the ADD project itself.

To enforce these permissions many commands require you to sign-in using your NERC/BAS user account. This process will
generate a user access token, valid for one hour, which allows this application to perform privileged actions on your
behalf.

For example, the `records publish` command can only be used by ADD data managers. Once you have signed-in and try to 
publish a record this application will check you have permission to publish records, returning an error if you don't.

ADD project staff can assign permissions to user as needed using the 
[Assigning permissions to users and groups](workflow-permissions-users.md) workflow.

If you have issues with permissions not working please raise an [issue](../README.md#issue-tracking).

**Note:** You will need an account within the NERC Active Directory to use this application. If you have a BAS email 
address you have an account and should use the same username and password you use for accessing your BAS email.

### Common errors

There are some common errors that can occur when using most commands:
   
#### `CSW catalogue not setup`

```
No. CSW catalogue not setup.
```

This error means the CSW catalogues for storing records have not been setup properly. This error should not occur and 
you should contact support (@felnne) if it occurs.

#### `Error with auth token`

```
No. Error with auth token. Try signing out and in again or seek support.
```

This error typically means your user auth token has expired and needs to refreshed by signing-in again. If this doesn't
fix the problem, you should contact support (@felnne).

#### `Missing auth token`

```
No. Missing auth token. Run `auth sign-in` first.
```

This error occurs when you try to use a command that requires permission to use and have not yet signed-in.

Use the [Sign-in](#auth-sign-in) command to fix this.

#### `Missing permissions in auth token`

```
No. Missing permissions in auth token. Seek support to assign required permissions.
```

This error occurs when you try to use a command that requires permissions you haven't been assigned. See the 
[Command permissions](#command-permissions) section for more information.

## `auth`

Manage user access to information and functions.

### `auth sign-in`

Set user access token to use application.

Running this command will return a code you will need to enter into a Microsoft website. This code is random and will
change each time you sign-in. It's used to help identify the application you are trying to sign into. The application
will wait until you tell it you've signed in.

When you enter the code into the website, you will be redirected to the standard NERC sign-in page (the same used for 
accessing Office 365) to enter your password.

The first time you use this application, you will be asked to allow the 'SCAR ADD Metadata Toolbox (Editor)' application
to access your basic account information (your name and email address). You need to approve this request to continue.

When you see this message:

> SCAR ADD Metadata Toolbox (Editor)
>
> You have signed in to the SCAR ADD Metadata Toolbox (Editor) application on your device. You may now close this window.

You can press any key to prompt the application to continue signing in. If successful you will see a success message 
with your name and the path to a file that contains your user access token, which you can ignore unless you have 
problems with permissions later.

You can sign-in again if you need to get a new user access token (if your permissions change for example). This will
override any existing token.

```
add-metadata-toolbox auth sign-in
To sign-in, visit 'https://microsoft.com/devicelogin', enter this code 'XXXXXXXXX' and then press any key...
Ok. Access token for 'Connie Watson' set in '/usr/src/app/auth.json'.
```

### `auth sign-out`

Remove existing access token if present.

In some cases you may want to intentionally clear your user access token, rather than allowing it to expire.

```
add-metadata-toolbox auth sign-out
Ok. Access token removed.
```

## `collections`
  
Manage site collections.

### `collections bulk-export`

Export all collections to files in a directory.

Collections will be saved as separate files named after their identifier, 
e.g. `e74543c0-4c4e-4b41-aa33-5bb2f67df389.json`

**Note:** The export directory must already exist.

```
add-metadata-toolbox collections bulk-export /tmp/collections/
1 collections to (re)export.
# Collection 1/1
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' exported.
Ok. 1 collections (re)exported.
```

If the directory you are exporting to already has exported collections you will get an error:

```
add-metadata-toolbox collections bulk-export /tmp/collections/
1 collections to (re)export.
# Collection 1/1
No. Export of collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' would be overwritten. Add `--allow-overwrite` flag to allow.
```

If you'd like to update them, add the `--allow-overwrite` option:

```
add-metadata-toolbox collections bulk-export /tmp/collections/ --allow-overwrite
1 collections to (re)export.
# Collection 1/1
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' re-exported.
Ok. 1 collections (re)exported.
```

### `collections bulk-import`

Import records from files in a directory.

```
add-metadata-toolbox collections bulk-import /tmp/collections/
1 collections to import/update.
# collection 1/1
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' imported.
Ok. 1 collections imported/updated.
```

If the directory you are importing from contains collections have already exist you will get an error:

```
add-metadata-toolbox collections bulk-import /tmp/collections/
1 collections to import/update.
# Collection 1/1
No. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' already exists. Add `--allow-update` flag to allow.
```

If you'd like to re-import and update them, add the `--allow-update` option:

```
add-metadata-toolbox collections bulk-import /tmp/collections/ --allow-update
1 collections to import/update.
# Collection 1/1
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' updated.
Ok. 1 collections imported/updated.
```

### `collections bulk-remove`

Remove all collections.

**WARNING!** Deleted collections cannot be recovered unless they have been exported as a backup first.

```
add-metadata-toolbox collections bulk-remove
CONFIRM: Permanently remove all 3 collections? [y/N]: y
1 collections to remove.
# Collection 1/1
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' removed.
Ok. 1 collections removed.
```

**Note:** This command uses an interactive conformation to protect against unintentional deletions. If using this 
command in a non-interactive environment you can add the `--force-remove` option to suppress this conformation.

### `collections export`

Export a collection to a file.

**Note:** Collections are exported as JSON files, therefore it's strongly recommended you export them to a file with 
the `.json` file extension.

```
add-metadata-toolbox collections export e74543c0-4c4e-4b41-aa33-5bb2f67df389 /tmp/collection.json
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' exported.
```

If the file you are exporting to already has exists you will get an error:

```
add-metadata-toolbox collections export e74543c0-4c4e-4b41-aa33-5bb2f67df389 /tmp/collection.json
No. Export of collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' would be overwritten. Add `--allow-overwrite` flag to allow.
```

If you'd like to update the file, add the `--allow-overwrite` option:

```
add-metadata-toolbox collections export e74543c0-4c4e-4b41-aa33-5bb2f67df389 /tmp/collection.json --allow-overwrite
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' re-exported.
```

### `collections import`

Import a collection from a file.

See the [Collections](../README.md#collections) README section for how to write a new collection.

```
add-metadata-toolbox collections import /tmp/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389.json
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' imported.
```

If the file you are importing contains a collection that already exists you will get an error:

```
add-metadata-toolbox collections import /tmp/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389.json
No. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' already exists. Add `--allow-update` flag to allow.
```

If you'd like to update the collection from the file, add the `--allow-update` option:

```
add-metadata-toolbox collections import /tmp/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389.json --allow-update
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' updated.
```

### `collections inspect`

View details for a collection.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox collections inspect e74543c0-4c4e-4b41-aa33-5bb2f67df389
Ok. Collection details for 'e74543c0-4c4e-4b41-aa33-5bb2f67df389':

Identifier: e74543c0-4c4e-4b41-aa33-5bb2f67df389
Title: SCAR Antarctic Digital Database (ADD)

Summary:
  The Scientific Committee on Antarctic Research (SCAR) Antarctic Digital Database (ADD) aims to provide a seamless topographic map compiled from the best available international geographic information for all areas. It covers Antarctica south of 60°S.

  The SCAR ADD consists of geographic information layers including:

  * coastline
  * ice-shelf grounding line
  * rock outcrop
  * contours

  See the [SCAR website](https://scar.org/data-products/antarctic-digital-database/) for more information.

Items in collection: 18
* 2cddeea3-eb67-46af-a002-8251337984d4 - Low resolution vector contours for Antarctica
* 2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23 - Medium resolution vector polygons of Antarctic rock outcrop
* 3a6d68fc-5a35-4f40-b45d-2268000031a4 - Medium resolution Antarctic moraine dataset
* 6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda - Medium resolution Antarctic lakes dataset
* 9ae21db4-49a9-409c-b48f-af597bbfec17 - High resolution Antarctic moraine dataset
* 862f7159-9e0d-46e2-9684-df1bf924dabc - Medium resolution vector polygons of the Antarctic coastline
* 8537f4c6-fc79-4d18-8877-dc2db9ee945e - High resolution Antarctic lakes dataset
* 33d5a2d4-66d8-46be-82c8-404664b21455 - High resolution vector polygons of the Antarctic coastline
* 87cf3067-befd-4a66-8b41-e3b5a60e2140 - Antarctic streams dataset
* 4149c45d-ce29-49f3-88ed-8366fe1afa23 - Automatically extracted rock outcrop dataset for Antarctica
* 8643fd87-cca5-4e56-bc81-46af208ef260 - Medium resolution vector contours for Antarctica
* 722521b8-22f3-4585-9f2a-a1c24212baef - Medium resolution vector polygon seamask for areas south of 60°S
* c1ed29bc-6136-4467-8357-00d426c8850c - Antarctic Digital Database data limit at 60°S
* d531a142-d6e7-4961-ab36-ab1db39f3f00 - High resolution vector polygons of Antarctic rock outcrop
* f58e3d6c-bc21-40fa-ab1a-a7798c9a8121 - High resolution vector contours for Antarctica
* 63501753-9578-4a61-b5a6-7024f5837182 - High resolution vector polylines of the Antarctic coastline
* c920561d-ec14-4e13-a5be-4c7a962b16cc - Medium resolution vector polylines of the Antarctic coastline
* dd6dd055-481e-4de2-8444-e00d7536f779 - High resolution vector polygon seamask for areas south of 60°S
```

### `collections list`

List all collections.
 
```
add-metadata-toolbox collections list

╒══════════════════════════════════════╤═══════════════════════════════════════╤═════════════════╕
│ Collection Identifier                │ Collection Title                      │   Items (count) │
╞══════════════════════════════════════╪═══════════════════════════════════════╪═════════════════╡
│ e74543c0-4c4e-4b41-aa33-5bb2f67df389 │ SCAR Antarctic Digital Database (ADD) │              18 │
╘══════════════════════════════════════╧═══════════════════════════════════════╧═════════════════╛

Ok. 1 collections.
```

### `collections remove`

Remove a collection.

**WARNING!** Deleted collections cannot be recovered unless they have been exported as a backup first.

```
add-metadata-toolbox collections remove e74543c0-4c4e-4b41-aa33-5bb2f67df389
Ok. Collection 'e74543c0-4c4e-4b41-aa33-5bb2f67df389' removed.
```

**Note:** This command uses an interactive conformation to protect against unintentional deletions. If using this 
command in a non-interactive environment you can add the `--force-remove` option to suppress this conformation.

## `csw`

Manage CSW catalogues.

### `csw setup`

Setup catalogue database structure.

This command requires the name of a CSW catalogue to initialise, for which valid options are:

* `published`
* `unpublished`

**Note:** This command only needs to be ran as part of setting up this application for the first time. 

```
add-metadata-toolbox csw setup unpublished
Ok. Catalogue 'unpublished' setup.
```

## `records`
  
Manage metadata records.

### `records bulk-export`

Export all records to files in a directory.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

Records will be saved as separate files named after their identifier, 
e.g. `2cddeea3-eb67-46af-a002-8251337984d4.json`

**Note:** The export directory must already exist.

```
add-metadata-toolbox records bulk-export /tmp/records/
18 records to (re)export.
# Record 1/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' exported.
# Record 2/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' exported.
# Record 3/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' exported.
# Record 4/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' exported.
# Record 5/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' exported.
# Record 6/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' exported.
# Record 7/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' exported.
# Record 8/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' exported.
# Record 9/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' exported.
# Record 10/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' exported.
# Record 11/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' exported.
# Record 12/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' exported.
# Record 13/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' exported.
# Record 14/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' exported.
# Record 15/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' exported.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' exported.
# Record 17/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' exported.
# Record 18/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' exported.
Ok. 18 records (re)exported.
```

If the directory you are exporting to already has exported records you will get an error:

```
add-metadata-toolbox records bulk-export /tmp/records/
18 records to (re)export.
# Record 1/18
No. Export of record '2cddeea3-eb67-46af-a002-8251337984d4' would be overwritten. Add `--allow-overwrite` flag to allow.
```

If you'd like to update them, add the `--allow-overwrite` option:

```
add-metadata-toolbox records bulk-export /tmp/records/ --allow-overwrite
18 records to (re)export.
# Record 1/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' re-exported.
# Record 2/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' re-exported.
# Record 3/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' re-exported.
# Record 4/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' re-exported.
# Record 5/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' re-exported.
# Record 6/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' re-exported.
# Record 7/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' re-exported.
# Record 8/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' re-exported.
# Record 9/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' re-exported.
# Record 10/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' re-exported.
# Record 11/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' re-exported.
# Record 12/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' re-exported.
# Record 13/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' re-exported.
# Record 14/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' re-exported.
# Record 15/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' re-exported.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' re-exported.
# Record 17/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' re-exported.
# Record 18/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' re-exported.
Ok. 18 records (re)exported.
```

### `records bulk-import`

Import records from files in a directory.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox records bulk-import /tmp/records
18 records to import/update.
# Record 1/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' imported.
# Record 2/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' imported.
# Record 3/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' imported.
# Record 4/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' imported.
# Record 5/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' imported.
# Record 6/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' imported.
# Record 7/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' imported.
# Record 8/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' imported.
# Record 9/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' imported.
# Record 10/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' imported.
# Record 11/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' imported.
# Record 12/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' imported.
# Record 13/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' imported.
# Record 14/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' imported.
# Record 15/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' imported.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' imported.
# Record 17/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' imported.
# Record 18/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' imported.
Ok. 18 records imported/updated.
```

If the directory you are importing from contains collections have already exist you will get an error:

```
add-metadata-toolbox records bulk-import /tmp/records
18 records to import/update.
# Record 1/18
No. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' already exists. Add `--allow-update` flag to allow.
```

If you'd like to re-import and update them, add the `--allow-update` option:

```
add-metadata-toolbox records bulk-import /tmp/records --allow-update
18 records to import/update.
# Record 1/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' updated.
# Record 2/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' updated.
# Record 3/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' updated.
# Record 4/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' updated.
# Record 5/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' updated.
# Record 6/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' updated.
# Record 7/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' updated.
# Record 8/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' updated.
# Record 9/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' updated.
# Record 10/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' updated.
# Record 11/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' updated.
# Record 12/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' updated.
# Record 13/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' updated.
# Record 14/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' updated.
# Record 15/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' updated.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' updated.
# Record 17/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' updated.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' updated.
Ok. 18 records imported/updated.
```

To automatically publish records after import add the `--publish` option:

```
add-metadata-toolbox records bulk-import /tmp/records --publish
18 records to import/update.
# Record 1/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' imported.
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' published.
# Record 2/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' imported.
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' published.
# Record 3/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' imported.
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' published.
# Record 4/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' imported.
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' published.
# Record 5/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' imported.
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' published.
# Record 6/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' imported.
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' published.
# Record 7/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' imported.
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' published.
# Record 8/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' imported.
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' published.
# Record 9/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' imported.
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' published.
# Record 10/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' imported.
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' published.
# Record 11/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' imported.
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' published.
# Record 12/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' imported.
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' published.
# Record 13/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' imported.
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' published.
# Record 14/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' imported.
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' published.
# Record 15/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' imported.
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' published.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' imported.
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' published.
# Record 17/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' imported.
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' published.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' imported.
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' published.
Ok. 18 records imported/updated.
```

Updated records will still be considered published (as they will have the same file identifier). To republish updated
records add the `--allow-republish` option.

```
add-metadata-toolbox records bulk-import /tmp/records --publish --allow-update --allow-republish
18 records to import/update.
# Record 1/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' updated.
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' republished.
# Record 2/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' updated.
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' republished.
# Record 3/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' updated.
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' republished.
# Record 4/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' updated.
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' republished.
# Record 5/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' updated.
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' republished.
# Record 6/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' updated.
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' republished.
# Record 7/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' updated.
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' republished.
# Record 8/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' updated.
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' republished.
# Record 9/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' updated.
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' republished.
# Record 10/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' updated.
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' republished.
# Record 11/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' updated.
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' republished.
# Record 12/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' updated.
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' republished.
# Record 13/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' updated.
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' republished.
# Record 14/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' updated.
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' republished.
# Record 15/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' updated.
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' republished.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' updated.
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' republished.
# Record 17/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' updated.
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' republished.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' updated.
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' republished.
Ok. 18 records imported/updated.
```

### `records bulk-publish`

Publish all (un)published records.

**Note:** You need to be signed in with permission to publish/retract metadata records to use this command.

```
add-metadata-toolbox records bulk-publish
18 records to (re)publish.
# Record 1/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' published.
# Record 2/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' published.
# Record 3/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' published.
# Record 4/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' published.
# Record 5/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' published.
# Record 6/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' published.
# Record 7/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' published.
# Record 8/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' published.
# Record 9/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' published.
# Record 10/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' published.
# Record 11/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' published.
# Record 12/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' published.
# Record 13/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' published.
# Record 14/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' published.
# Record 15/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' published.
# Record 16/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' published.
# Record 17/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' published.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' published.
Ok. 18 records (re)published.
```

By default only unpublished records will be published. To republish all records instead add the `--force-republish` 
option:

```
18 records to (re)publish.
# Record 1/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' republished.
# Record 2/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' republished.
# Record 3/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' republished.
# Record 4/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' republished.
# Record 5/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' republished.
# Record 6/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' republished.
# Record 7/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' republished.
# Record 8/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' republished.
# Record 9/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' republished.
# Record 10/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' republished.
# Record 11/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' republished.
# Record 12/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' republished.
# Record 13/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' republished.
# Record 14/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' republished.
# Record 15/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' republished.
# Record 16/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' republished.
# Record 17/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' republished.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' republished.
Ok. 18 records (re)published.
```

### `records bulk-remove`

Remove all unpublished records.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

**Note:** You need to retract all records before you can remove them.

**WARNING!** Deleted records cannot be recovered unless they have been exported as a backup first.

```
add-metadata-toolbox records bulk-remove
CONFIRM: Permanently remove all 18 unpublished records? [y/N]: y
18 records to remove.
# Record 1/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' removed.
# Record 2/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' removed.
# Record 3/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' removed.
# Record 4/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' removed.
# Record 5/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' removed.
# Record 6/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' removed.
# Record 7/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' removed.
# Record 8/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' removed.
# Record 9/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' removed.
# Record 10/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' removed.
# Record 11/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' removed.
# Record 12/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' removed.
# Record 13/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' removed.
# Record 14/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' removed.
# Record 15/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' removed.
# Record 16/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' removed.
# Record 17/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' removed.
# Record 18/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' removed.
Ok. 18 records removed.
```

### `records bulk-retract`

Retract all published records.

**Note:** You need to be signed in with permission to publish/retract metadata records to use this command.

```
add-metadata-toolbox records bulk-retract
18 records to retract.
# Record 1/18
Ok. Record 'c1ed29bc-6136-4467-8357-00d426c8850c' retracted.
# Record 2/18
Ok. Record 'dd6dd055-481e-4de2-8444-e00d7536f779' retracted.
# Record 3/18
Ok. Record '862f7159-9e0d-46e2-9684-df1bf924dabc' retracted.
# Record 4/18
Ok. Record 'd531a142-d6e7-4961-ab36-ab1db39f3f00' retracted.
# Record 5/18
Ok. Record '8537f4c6-fc79-4d18-8877-dc2db9ee945e' retracted.
# Record 6/18
Ok. Record '722521b8-22f3-4585-9f2a-a1c24212baef' retracted.
# Record 7/18
Ok. Record '33d5a2d4-66d8-46be-82c8-404664b21455' retracted.
# Record 8/18
Ok. Record '9ae21db4-49a9-409c-b48f-af597bbfec17' retracted.
# Record 9/18
Ok. Record '3a6d68fc-5a35-4f40-b45d-2268000031a4' retracted.
# Record 10/18
Ok. Record '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' retracted.
# Record 11/18
Ok. Record 'c920561d-ec14-4e13-a5be-4c7a962b16cc' retracted.
# Record 12/18
Ok. Record '87cf3067-befd-4a66-8b41-e3b5a60e2140' retracted.
# Record 13/18
Ok. Record '2cddeea3-eb67-46af-a002-8251337984d4' retracted.
# Record 14/18
Ok. Record '63501753-9578-4a61-b5a6-7024f5837182' retracted.
# Record 15/18
Ok. Record '8643fd87-cca5-4e56-bc81-46af208ef260' retracted.
# Record 16/18
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' retracted.
# Record 17/18
Ok. Record '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' retracted.
# Record 18/18
Ok. Record 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' retracted.
Ok. 18 records retracted.
```

### `records export`

Export a record to a file.

**Note:** You need to be signed in with permission to publish metadata records to use this command.

**Note:** Records are exported as JSON files, therefore it's strongly recommended you export them to a file with the 
`.json` file extension.

```
add-metadata-toolbox records export 4149c45d-ce29-49f3-88ed-8366fe1afa23 /tmp/record.json
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' exported.
```

If the file you are exporting to already has exists you will get an error:

```
add-metadata-toolbox records export 4149c45d-ce29-49f3-88ed-8366fe1afa23 /tmp/record.json
No. Export of record '4149c45d-ce29-49f3-88ed-8366fe1afa23' would be overwritten. Add `--allow-overwrite` flag to allow.
```

If you'd like to update the file, add the `--allow-overwrite` option:

```
add-metadata-toolbox collections export e74543c0-4c4e-4b41-aa33-5bb2f67df389 /tmp/collection.json --allow-overwrite
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' re-exported.
```

### `records import`

Import a record from a file.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

See the [Provisional guidance (internal)](https://gitlab.data.bas.ac.uk/MAGIC/add/-/issues/146#note_49157) for how to 
write a new record.

```
add-metadata-toolbox records import /tmp/record.json
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' imported.
```

If the file you are importing contains a record that already exists you will get an error:

```
add-metadata-toolbox records import /tmp/record.json
No. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' already exists. Add `--allow-update` flag to allow.
```

If you'd like to update the record from the file, add the `--allow-update` option:

```
add-metadata-toolbox records import /tmp/record.json --allow-update
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' updated.
```

To automatically publish the record after import add the `--publish` option:

```
add-metadata-toolbox records import /tmp/record.json --publish
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' imported.
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' published.
```

An updated record will still be considered published (as they will have the same file identifier). To republish an 
updated record add the `--allow-republish` option.

```
add-metadata-toolbox records import /tmp/record.json --publish --allow-update --allow-republish
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' updated.
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' republished.
```

### `records list`

List all records.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox records list

╒══════════════════════════════════════╤══════════════════════════════════════════════════════════════════╤═════════════╕
│ Record Identifier                    │ Record Title                                                     │ Status      │
╞══════════════════════════════════════╪══════════════════════════════════════════════════════════════════╪═════════════╡
│ 862f7159-9e0d-46e2-9684-df1bf924dabc │ Medium resolution vector polygons of the Antarctic coastline     │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 722521b8-22f3-4585-9f2a-a1c24212baef │ Medium resolution vector polygon seamask for areas south of 60°S │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ d531a142-d6e7-4961-ab36-ab1db39f3f00 │ High resolution vector polygons of Antarctic rock outcrop        │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 33d5a2d4-66d8-46be-82c8-404664b21455 │ High resolution vector polygons of the Antarctic coastline       │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 9ae21db4-49a9-409c-b48f-af597bbfec17 │ High resolution Antarctic moraine dataset                        │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23 │ Medium resolution vector polygons of Antarctic rock outcrop      │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 4149c45d-ce29-49f3-88ed-8366fe1afa23 │ Automatically extracted rock outcrop dataset for Antarctica      │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ dd6dd055-481e-4de2-8444-e00d7536f779 │ High resolution vector polygon seamask for areas south of 60°S   │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 63501753-9578-4a61-b5a6-7024f5837182 │ High resolution vector polylines of the Antarctic coastline      │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ c1ed29bc-6136-4467-8357-00d426c8850c │ Antarctic Digital Database data limit at 60°S                    │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda │ Medium resolution Antarctic lakes dataset                        │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ c920561d-ec14-4e13-a5be-4c7a962b16cc │ Medium resolution vector polylines of the Antarctic coastline    │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ f58e3d6c-bc21-40fa-ab1a-a7798c9a8121 │ High resolution vector contours for Antarctica                   │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 87cf3067-befd-4a66-8b41-e3b5a60e2140 │ Antarctic streams dataset                                        │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 8643fd87-cca5-4e56-bc81-46af208ef260 │ Medium resolution vector contours for Antarctica                 │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 3a6d68fc-5a35-4f40-b45d-2268000031a4 │ Medium resolution Antarctic moraine dataset                      │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 8537f4c6-fc79-4d18-8877-dc2db9ee945e │ High resolution Antarctic lakes dataset                          │ Published   │
├──────────────────────────────────────┼──────────────────────────────────────────────────────────────────┼─────────────┤
│ 2cddeea3-eb67-46af-a002-8251337984d4 │ Low resolution vector contours for Antarctica                    │ Published   │
╘══════════════════════════════════════╧══════════════════════════════════════════════════════════════════╧═════════════╛

Ok. 18 records.
```

### `records publish`

Publish a record.

**Note:** You need to be signed in with permission to publish/retract metadata records to use this command.

```
add-metadata-toolbox records publish 4149c45d-ce29-49f3-88ed-8366fe1afa23
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' published.
```

If the record you are publishing has already been published you will get an error:

```
add-metadata-toolbox records publish 4149c45d-ce29-49f3-88ed-8366fe1afa23
No. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' already published. Add `--allow-republish` flag to allow.
```

If you'd like to republish the record to match its unpublished version, add the `--allow-republish` option:

```
add-metadata-toolbox records publish 4149c45d-ce29-49f3-88ed-8366fe1afa23 --allow-republish
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' republished.
```

### `records remove`

Remove an unpublished record.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

**Note:** You need to retract the record before you can remove it.

**WARNING!** Deleted records cannot be recovered unless they have been exported as a backup first.

```
add-metadata-toolbox records remove 4149c45d-ce29-49f3-88ed-8366fe1afa23
CONFIRM: Permanently remove record '4149c45d-ce29-49f3-88ed-8366fe1afa23'? [y/N]: y
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' removed.
```

**Note:** This command uses an interactive conformation to protect against unintentional deletions. If using this 
command in a non-interactive environment you can add the `--force-remove` option to suppress this conformation.

### `records retract`

Retract a published record.

**Note:** You need to be signed in with permission to publish/retract metadata records to use this command.

```
add-metadata-toolbox records retract 4149c45d-ce29-49f3-88ed-8366fe1afa23
Ok. Record '4149c45d-ce29-49f3-88ed-8366fe1afa23' retracted.
```

## `routes`

**Note:** This command should be ignored. It's part of the framework used to build this application and can't be hidden.

## `run`

**Note:** This command should be ignored. It's part of the framework used to build this application and can't be hidden.

## `seed`
  
Manage sample resources for testing.

**Note:** These commands should only be used during development.

### `seed collections`

Create sample collections for testing.

Generates a given number of collections using fake data. A random number of records will be added to each collection,
this command should therefore be ran after seeding records.

```
add-metadata-toolbox seed collections 3
3 collections to insert.
# Collection 1/3
Ok. Inserted collection '1a2296cc-a3c1-4085-ab0a-5d04da4abd6f.
# Collection 2/3
Ok. Inserted collection 'c137ac4f-e992-4563-95a2-0f1202233257.
# Collection 3/3
Ok. Inserted collection '6d670c11-e700-4675-af08-405e70ef1c9f.
Ok. Inserted 3 collections.
```

### `seed records`

Create sample records for testing.

Generates a given number of records using fake data.

```
add-metadata-toolbox seed records 3
3 records to insert.
# Record 1/3
Ok. Inserted record '17b41473-184f-4f63-8ee4-b99f00312c88.
# Record 2/3
Ok. Inserted record '00cd7eeb-70f3-481b-8f1d-aeab92199080.
# Record 3/3
Ok. Inserted record 'd146c907-3abb-447e-9ed8-d61bc547e509.
Ok. Inserted 3 records.
```

## `shell`

**Note:** This command should be ignored. It's part of the framework used to build this application and can't be hidden.

## `site`

Manage static site.

### `site build            `

Build all static site components.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox site build
54 record pages to generate.
# Record page 1/18 (stylesheet 1/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-html').
# Record page 1/18 (stylesheet 2/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-rubric').
# Record page 1/18 (stylesheet 3/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-xml').
# Record page 2/18 (stylesheet 1/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-html').
# Record page 2/18 (stylesheet 2/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-rubric').
# Record page 2/18 (stylesheet 3/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-xml').
# Record page 3/18 (stylesheet 1/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-html').
# Record page 3/18 (stylesheet 2/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-rubric').
# Record page 3/18 (stylesheet 3/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-xml').
# Record page 4/18 (stylesheet 1/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-html').
# Record page 4/18 (stylesheet 2/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-rubric').
# Record page 4/18 (stylesheet 3/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-xml').
# Record page 5/18 (stylesheet 1/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-html').
# Record page 5/18 (stylesheet 2/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-rubric').
# Record page 5/18 (stylesheet 3/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-xml').
# Record page 6/18 (stylesheet 1/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-html').
# Record page 6/18 (stylesheet 2/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-rubric').
# Record page 6/18 (stylesheet 3/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-xml').
# Record page 7/18 (stylesheet 1/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-html').
# Record page 7/18 (stylesheet 2/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-rubric').
# Record page 7/18 (stylesheet 3/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-xml').
# Record page 8/18 (stylesheet 1/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-html').
# Record page 8/18 (stylesheet 2/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-rubric').
# Record page 8/18 (stylesheet 3/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-xml').
# Record page 9/18 (stylesheet 1/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-html').
# Record page 9/18 (stylesheet 2/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-rubric').
# Record page 9/18 (stylesheet 3/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-xml').
# Record page 10/18 (stylesheet 1/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-html').
# Record page 10/18 (stylesheet 2/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-rubric').
# Record page 10/18 (stylesheet 3/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-xml').
# Record page 11/18 (stylesheet 1/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-html').
# Record page 11/18 (stylesheet 2/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-rubric').
# Record page 11/18 (stylesheet 3/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-xml').
# Record page 12/18 (stylesheet 1/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-html').
# Record page 12/18 (stylesheet 2/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-rubric').
# Record page 12/18 (stylesheet 3/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-xml').
# Record page 13/18 (stylesheet 1/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-html').
# Record page 13/18 (stylesheet 2/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-rubric').
# Record page 13/18 (stylesheet 3/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-xml').
# Record page 14/18 (stylesheet 1/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-html').
# Record page 14/18 (stylesheet 2/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-rubric').
# Record page 14/18 (stylesheet 3/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-xml').
# Record page 15/18 (stylesheet 1/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-html').
# Record page 15/18 (stylesheet 2/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-rubric').
# Record page 15/18 (stylesheet 3/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-xml').
# Record page 16/18 (stylesheet 1/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-html').
# Record page 16/18 (stylesheet 2/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-rubric').
# Record page 16/18 (stylesheet 3/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-xml').
# Record page 17/18 (stylesheet 1/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-html').
# Record page 17/18 (stylesheet 2/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-rubric').
# Record page 17/18 (stylesheet 3/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-xml').
# Record page 18/18 (stylesheet 1/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-html').
# Record page 18/18 (stylesheet 2/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-rubric').
# Record page 18/18 (stylesheet 3/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-xml').
Ok. 54 record pages generated.
18 item pages to generate.
# Item page 1/18
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc'.
# Item page 2/18
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef'.
# Item page 3/18
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00'.
# Item page 4/18
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455'.
# Item page 5/18
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17'.
# Item page 6/18
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23'.
# Item page 7/18
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23'.
# Item page 8/18
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779'.
# Item page 9/18
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182'.
# Item page 10/18
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c'.
# Item page 11/18
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda'.
# Item page 12/18
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc'.
# Item page 13/18
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121'.
# Item page 14/18
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140'.
# Item page 15/18
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260'.
# Item page 16/18
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4'.
# Item page 17/18
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e'.
# Item page 18/18
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4'.
Ok. 18 item pages generated.
1 collection pages to generate.
# Collection page 1/1
  [####################################]  100%          
Ok. Generated collection page for 'e74543c0-4c4e-4b41-aa33-5bb2f67df389'.
Ok. 1 collection pages generated.
3 legal pages to generate.
# Legal page 1/3
Ok. Generated legal page for 'cookies'.
# Legal page 2/3
Ok. Generated legal page for 'copyright'.
# Legal page 3/3
Ok. Generated legal page for 'privacy'.
Ok. 3 legal pages generated.
Ok. feedback page generated.
Ok. static assets copied.
Ok. Site built.
```

### `site build-collections`

Build pages for all collections.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox site build-collections
1 collection pages to generate.
# Collection page 1/1
  [####################################]  100%          
Ok. Generated collection page for 'e74543c0-4c4e-4b41-aa33-5bb2f67df389'.
Ok. 1 collection pages generated.
```

### `site build-items`

Build pages for all items.

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox site build-items
18 item pages to generate.
# Item page 1/18
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc'.
# Item page 2/18
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef'.
# Item page 3/18
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00'.
# Item page 4/18
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455'.
# Item page 5/18
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17'.
# Item page 6/18
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23'.
# Item page 7/18
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23'.
# Item page 8/18
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779'.
# Item page 9/18
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182'.
# Item page 10/18
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c'.
# Item page 11/18
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda'.
# Item page 12/18
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc'.
# Item page 13/18
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121'.
# Item page 14/18
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140'.
# Item page 15/18
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260'.
# Item page 16/18
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4'.
# Item page 17/18
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e'.
# Item page 18/18
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4'.
Ok. 18 item pages generated.
```

### `site build-pages`

Build pages for legal policies and feedback form.

```
add-metadata-toolbox site build-pages
3 legal pages to generate.
# Legal page 1/3
Ok. Generated legal page for 'cookies'.
# Legal page 2/3
Ok. Generated legal page for 'copyright'.
# Legal page 3/3
Ok. Generated legal page for 'privacy'.
Ok. 3 legal pages generated.
Ok. feedback page generated.
```

### `site build-records`

Build pages for all records (XML).

**Note:** You need to be signed in with permission to edit metadata records to use this command.

```
add-metadata-toolbox site build-records
54 record pages to generate.
# Record page 1/18 (stylesheet 1/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-html').
# Record page 1/18 (stylesheet 2/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-rubric').
# Record page 1/18 (stylesheet 3/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-xml').
# Record page 2/18 (stylesheet 1/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-html').
# Record page 2/18 (stylesheet 2/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-rubric').
# Record page 2/18 (stylesheet 3/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-xml').
# Record page 3/18 (stylesheet 1/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-html').
# Record page 3/18 (stylesheet 2/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-rubric').
# Record page 3/18 (stylesheet 3/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-xml').
# Record page 4/18 (stylesheet 1/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-html').
# Record page 4/18 (stylesheet 2/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-rubric').
# Record page 4/18 (stylesheet 3/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-xml').
# Record page 5/18 (stylesheet 1/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-html').
# Record page 5/18 (stylesheet 2/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-rubric').
# Record page 5/18 (stylesheet 3/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-xml').
# Record page 6/18 (stylesheet 1/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-html').
# Record page 6/18 (stylesheet 2/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-rubric').
# Record page 6/18 (stylesheet 3/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-xml').
# Record page 7/18 (stylesheet 1/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-html').
# Record page 7/18 (stylesheet 2/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-rubric').
# Record page 7/18 (stylesheet 3/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-xml').
# Record page 8/18 (stylesheet 1/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-html').
# Record page 8/18 (stylesheet 2/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-rubric').
# Record page 8/18 (stylesheet 3/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-xml').
# Record page 9/18 (stylesheet 1/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-html').
# Record page 9/18 (stylesheet 2/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-rubric').
# Record page 9/18 (stylesheet 3/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-xml').
# Record page 10/18 (stylesheet 1/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-html').
# Record page 10/18 (stylesheet 2/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-rubric').
# Record page 10/18 (stylesheet 3/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-xml').
# Record page 11/18 (stylesheet 1/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-html').
# Record page 11/18 (stylesheet 2/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-rubric').
# Record page 11/18 (stylesheet 3/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-xml').
# Record page 12/18 (stylesheet 1/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-html').
# Record page 12/18 (stylesheet 2/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-rubric').
# Record page 12/18 (stylesheet 3/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-xml').
# Record page 13/18 (stylesheet 1/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-html').
# Record page 13/18 (stylesheet 2/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-rubric').
# Record page 13/18 (stylesheet 3/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-xml').
# Record page 14/18 (stylesheet 1/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-html').
# Record page 14/18 (stylesheet 2/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-rubric').
# Record page 14/18 (stylesheet 3/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-xml').
# Record page 15/18 (stylesheet 1/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-html').
# Record page 15/18 (stylesheet 2/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-rubric').
# Record page 15/18 (stylesheet 3/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-xml').
# Record page 16/18 (stylesheet 1/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-html').
# Record page 16/18 (stylesheet 2/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-rubric').
# Record page 16/18 (stylesheet 3/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-xml').
# Record page 17/18 (stylesheet 1/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-html').
# Record page 17/18 (stylesheet 2/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-rubric').
# Record page 17/18 (stylesheet 3/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-xml').
# Record page 18/18 (stylesheet 1/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-html').
# Record page 18/18 (stylesheet 2/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-rubric').
# Record page 18/18 (stylesheet 3/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-xml').
Ok. 54 record pages generated.
```

### `site copy-assets`

Copy all static assets (CSS, JS, etc.).

```
add-metadata-toolbox site copy-assets
Ok. static assets copied.
```

### `site publish`

Publish static site build to remote location.

**WARNING:** This will replace the contents of the static site. 

```
add-metadata-toolbox site publish
CONFIRM: Publish static site to 'add-catalogue-integration.data.bas.ac.uk'? [y/N]: y
upload: _site/collections/1790c9d5-af77-4a03-9a08-6ba8e83ce748/index.html to s3://add-catalogue-integration.data.bas.ac.uk/collections/1790c9d5-af77-4a03-9a08-6ba8e83ce748/index.html
delete: s3://add-catalogue-integration.data.bas.ac.uk/collections/4d62ce11-fc98-4aca-9564-8abe11d79d9a/index.html
upload: _site/items/0857a464-e7d9-422f-baf7-02c2d38023bb/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/0857a464-e7d9-422f-baf7-02c2d38023bb/index.html
upload: _site/collections/e48af7be-8289-4719-a4ed-063c6fef07c1/index.html to s3://add-catalogue-integration.data.bas.ac.uk/collections/e48af7be-8289-4719-a4ed-063c6fef07c1/index.html
upload: _site/feedback/index.html to s3://add-catalogue-integration.data.bas.ac.uk/feedback/index.html
upload: _site/collections/b8aedf99-0c7f-4d3c-ba6e-d7e3ee746a4d/index.html to s3://add-catalogue-integration.data.bas.ac.uk/collections/b8aedf99-0c7f-4d3c-ba6e-d7e3ee746a4d/index.html
upload: _site/items/63501753-9578-4a61-b5a6-7024f5837182/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/63501753-9578-4a61-b5a6-7024f5837182/index.html
upload: _site/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/index.html to s3://add-catalogue-integration.data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/index.html
upload: _site/items/8537f4c6-fc79-4d18-8877-dc2db9ee945e/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/8537f4c6-fc79-4d18-8877-dc2db9ee945e/index.html
upload: _site/items/33d5a2d4-66d8-46be-82c8-404664b21455/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/33d5a2d4-66d8-46be-82c8-404664b21455/index.html
upload: _site/items/2cddeea3-eb67-46af-a002-8251337984d4/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/2cddeea3-eb67-46af-a002-8251337984d4/index.html
upload: _site/items/87cf3067-befd-4a66-8b41-e3b5a60e2140/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/87cf3067-befd-4a66-8b41-e3b5a60e2140/index.html
upload: _site/items/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/index.html
upload: _site/items/722521b8-22f3-4585-9f2a-a1c24212baef/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/722521b8-22f3-4585-9f2a-a1c24212baef/index.html
upload: _site/items/4149c45d-ce29-49f3-88ed-8366fe1afa23/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/4149c45d-ce29-49f3-88ed-8366fe1afa23/index.html
upload: _site/items/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/index.html
upload: _site/items/862f7159-9e0d-46e2-9684-df1bf924dabc/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/862f7159-9e0d-46e2-9684-df1bf924dabc/index.html
upload: _site/items/8643fd87-cca5-4e56-bc81-46af208ef260/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/8643fd87-cca5-4e56-bc81-46af208ef260/index.html
upload: _site/items/c920561d-ec14-4e13-a5be-4c7a962b16cc/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/c920561d-ec14-4e13-a5be-4c7a962b16cc/index.html
upload: _site/legal/privacy/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/privacy/index.html
upload: _site/legal/cookies/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/cookies/index.html
upload: _site/items/9ae21db4-49a9-409c-b48f-af597bbfec17/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/9ae21db4-49a9-409c-b48f-af597bbfec17/index.html
upload: _site/items/c1ed29bc-6136-4467-8357-00d426c8850c/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/c1ed29bc-6136-4467-8357-00d426c8850c/index.html
upload: _site/items/e40e8455-cb4c-43f5-97be-e91b1caedf66/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/e40e8455-cb4c-43f5-97be-e91b1caedf66/index.html
upload: _site/legal/copyright/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/copyright/index.html
upload: _site/items/dd6dd055-481e-4de2-8444-e00d7536f779/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/dd6dd055-481e-4de2-8444-e00d7536f779/index.html
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-html/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-html/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/items/d531a142-d6e7-4961-ab36-ab1db39f3f00/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/d531a142-d6e7-4961-ab36-ab1db39f3f00/index.html
upload: _site/items/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/index.html
upload: _site/items/3a6d68fc-5a35-4f40-b45d-2268000031a4/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/3a6d68fc-5a35-4f40-b45d-2268000031a4/index.html
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-rubric/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-rubric/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-rubric/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-rubric/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-html/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-html/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-rubric/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-rubric/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-xml/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-xml/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-xml/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-xml/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-html/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-html/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-html/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-html/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-rubric/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-rubric/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-xml/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-xml/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-html/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-html/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-rubric/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-rubric/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-rubric/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-rubric/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-html/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-html/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-xml/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-xml/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-html/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-html/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-rubric/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-rubric/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-xml/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-xml/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-rubric/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-rubric/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-xml/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-xml/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-xml/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-xml/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-xml/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-xml/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-html/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-html/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-html/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-html/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-rubric/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-rubric/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-html/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-html/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-xml/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-xml/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-rubric/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-rubric/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-rubric/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-rubric/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-xml/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-xml/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-html/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-html/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-html/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-html/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-rubric/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-rubric/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-rubric/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-rubric/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-xml/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-xml/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-xml/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-xml/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-rubric/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-rubric/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-xml/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-xml/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-xml/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-xml/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-xml/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-xml/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-html/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-html/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-rubric/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-rubric/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-xml/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-xml/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-rubric/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-rubric/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-html/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-html/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-xml/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-xml/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-html/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-html/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-rubric/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-rubric/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-html/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-html/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-html/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-html/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-rubric/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-rubric/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-html/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-html/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/static/css/app.css to s3://add-catalogue-integration.data.bas.ac.uk/static/css/app.css
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-xml/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-xml/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/static/js/item.js to s3://add-catalogue-integration.data.bas.ac.uk/static/js/item.js
upload: _site/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-html/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/e40e8455-cb4c-43f5-97be-e91b1caedf66/iso-html/e40e8455-cb4c-43f5-97be-e91b1caedf66.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-rubric/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-rubric/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-xml/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-xml/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
Ok. Site published to 'add-catalogue-integration.data.bas.ac.uk'
```

**Note:** This command uses an interactive conformation to protect against publishing to the wrong location 
unintentionally. If using this command in a non-interactive environment you can add the `--force-publish` option to 
suppress this conformation.

To build site content and the publish it, add the `--build` option.

**Note:** You need to be signed in with permission to edit metadata records to use this option.

```
add-metadata-toolbox site publish --build
54 record pages to generate.
# Record page 1/18 (stylesheet 1/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-html').
# Record page 1/18 (stylesheet 2/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-rubric').
# Record page 1/18 (stylesheet 3/3)
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc' (stylesheet 'iso-xml').
# Record page 2/18 (stylesheet 1/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-html').
# Record page 2/18 (stylesheet 2/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-rubric').
# Record page 2/18 (stylesheet 3/3)
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef' (stylesheet 'iso-xml').
# Record page 3/18 (stylesheet 1/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-html').
# Record page 3/18 (stylesheet 2/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-rubric').
# Record page 3/18 (stylesheet 3/3)
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00' (stylesheet 'iso-xml').
# Record page 4/18 (stylesheet 1/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-html').
# Record page 4/18 (stylesheet 2/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-rubric').
# Record page 4/18 (stylesheet 3/3)
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455' (stylesheet 'iso-xml').
# Record page 5/18 (stylesheet 1/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-html').
# Record page 5/18 (stylesheet 2/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-rubric').
# Record page 5/18 (stylesheet 3/3)
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17' (stylesheet 'iso-xml').
# Record page 6/18 (stylesheet 1/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-html').
# Record page 6/18 (stylesheet 2/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-rubric').
# Record page 6/18 (stylesheet 3/3)
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23' (stylesheet 'iso-xml').
# Record page 7/18 (stylesheet 1/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-html').
# Record page 7/18 (stylesheet 2/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-rubric').
# Record page 7/18 (stylesheet 3/3)
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23' (stylesheet 'iso-xml').
# Record page 8/18 (stylesheet 1/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-html').
# Record page 8/18 (stylesheet 2/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-rubric').
# Record page 8/18 (stylesheet 3/3)
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779' (stylesheet 'iso-xml').
# Record page 9/18 (stylesheet 1/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-html').
# Record page 9/18 (stylesheet 2/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-rubric').
# Record page 9/18 (stylesheet 3/3)
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182' (stylesheet 'iso-xml').
# Record page 10/18 (stylesheet 1/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-html').
# Record page 10/18 (stylesheet 2/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-rubric').
# Record page 10/18 (stylesheet 3/3)
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c' (stylesheet 'iso-xml').
# Record page 11/18 (stylesheet 1/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-html').
# Record page 11/18 (stylesheet 2/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-rubric').
# Record page 11/18 (stylesheet 3/3)
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda' (stylesheet 'iso-xml').
# Record page 12/18 (stylesheet 1/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-html').
# Record page 12/18 (stylesheet 2/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-rubric').
# Record page 12/18 (stylesheet 3/3)
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc' (stylesheet 'iso-xml').
# Record page 13/18 (stylesheet 1/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-html').
# Record page 13/18 (stylesheet 2/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-rubric').
# Record page 13/18 (stylesheet 3/3)
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121' (stylesheet 'iso-xml').
# Record page 14/18 (stylesheet 1/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-html').
# Record page 14/18 (stylesheet 2/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-rubric').
# Record page 14/18 (stylesheet 3/3)
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140' (stylesheet 'iso-xml').
# Record page 15/18 (stylesheet 1/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-html').
# Record page 15/18 (stylesheet 2/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-rubric').
# Record page 15/18 (stylesheet 3/3)
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260' (stylesheet 'iso-xml').
# Record page 16/18 (stylesheet 1/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-html').
# Record page 16/18 (stylesheet 2/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-rubric').
# Record page 16/18 (stylesheet 3/3)
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4' (stylesheet 'iso-xml').
# Record page 17/18 (stylesheet 1/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-html').
# Record page 17/18 (stylesheet 2/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-rubric').
# Record page 17/18 (stylesheet 3/3)
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e' (stylesheet 'iso-xml').
# Record page 18/18 (stylesheet 1/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-html').
# Record page 18/18 (stylesheet 2/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-rubric').
# Record page 18/18 (stylesheet 3/3)
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4' (stylesheet 'iso-xml').
Ok. 54 record pages generated.
18 item pages to generate.
# Item page 1/18
Ok. Generated item page for '862f7159-9e0d-46e2-9684-df1bf924dabc'.
# Item page 2/18
Ok. Generated item page for '722521b8-22f3-4585-9f2a-a1c24212baef'.
# Item page 3/18
Ok. Generated item page for 'd531a142-d6e7-4961-ab36-ab1db39f3f00'.
# Item page 4/18
Ok. Generated item page for '33d5a2d4-66d8-46be-82c8-404664b21455'.
# Item page 5/18
Ok. Generated item page for '9ae21db4-49a9-409c-b48f-af597bbfec17'.
# Item page 6/18
Ok. Generated item page for '2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23'.
# Item page 7/18
Ok. Generated item page for '4149c45d-ce29-49f3-88ed-8366fe1afa23'.
# Item page 8/18
Ok. Generated item page for 'dd6dd055-481e-4de2-8444-e00d7536f779'.
# Item page 9/18
Ok. Generated item page for '63501753-9578-4a61-b5a6-7024f5837182'.
# Item page 10/18
Ok. Generated item page for 'c1ed29bc-6136-4467-8357-00d426c8850c'.
# Item page 11/18
Ok. Generated item page for '6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda'.
# Item page 12/18
Ok. Generated item page for 'c920561d-ec14-4e13-a5be-4c7a962b16cc'.
# Item page 13/18
Ok. Generated item page for 'f58e3d6c-bc21-40fa-ab1a-a7798c9a8121'.
# Item page 14/18
Ok. Generated item page for '87cf3067-befd-4a66-8b41-e3b5a60e2140'.
# Item page 15/18
Ok. Generated item page for '8643fd87-cca5-4e56-bc81-46af208ef260'.
# Item page 16/18
Ok. Generated item page for '3a6d68fc-5a35-4f40-b45d-2268000031a4'.
# Item page 17/18
Ok. Generated item page for '8537f4c6-fc79-4d18-8877-dc2db9ee945e'.
# Item page 18/18
Ok. Generated item page for '2cddeea3-eb67-46af-a002-8251337984d4'.
Ok. 18 item pages generated.
1 collection pages to generate.
# Collection page 1/1
  [####################################]  100%          
Ok. Generated collection page for 'e74543c0-4c4e-4b41-aa33-5bb2f67df389'.
Ok. 1 collection pages generated.
3 legal pages to generate.
# Legal page 1/3
Ok. Generated legal page for 'cookies'.
# Legal page 2/3
Ok. Generated legal page for 'copyright'.
# Legal page 3/3
Ok. Generated legal page for 'privacy'.
Ok. 3 legal pages generated.
Ok. feedback page generated.
Ok. static assets copied.
Ok. Site built.
CONFIRM: Publish static site to 'add-catalogue-integration.data.bas.ac.uk'? [y/N]: y
upload: _site/feedback/index.html to s3://add-catalogue-integration.data.bas.ac.uk/feedback/index.html
upload: _site/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/index.html to s3://add-catalogue-integration.data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/index.html
upload: _site/items/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/index.html
upload: _site/items/4149c45d-ce29-49f3-88ed-8366fe1afa23/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/4149c45d-ce29-49f3-88ed-8366fe1afa23/index.html
upload: _site/items/8643fd87-cca5-4e56-bc81-46af208ef260/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/8643fd87-cca5-4e56-bc81-46af208ef260/index.html
upload: _site/items/87cf3067-befd-4a66-8b41-e3b5a60e2140/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/87cf3067-befd-4a66-8b41-e3b5a60e2140/index.html
upload: _site/items/9ae21db4-49a9-409c-b48f-af597bbfec17/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/9ae21db4-49a9-409c-b48f-af597bbfec17/index.html
upload: _site/items/862f7159-9e0d-46e2-9684-df1bf924dabc/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/862f7159-9e0d-46e2-9684-df1bf924dabc/index.html
upload: _site/items/8537f4c6-fc79-4d18-8877-dc2db9ee945e/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/8537f4c6-fc79-4d18-8877-dc2db9ee945e/index.html
upload: _site/items/2cddeea3-eb67-46af-a002-8251337984d4/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/2cddeea3-eb67-46af-a002-8251337984d4/index.html
upload: _site/items/c1ed29bc-6136-4467-8357-00d426c8850c/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/c1ed29bc-6136-4467-8357-00d426c8850c/index.html
upload: _site/items/33d5a2d4-66d8-46be-82c8-404664b21455/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/33d5a2d4-66d8-46be-82c8-404664b21455/index.html
upload: _site/items/c920561d-ec14-4e13-a5be-4c7a962b16cc/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/c920561d-ec14-4e13-a5be-4c7a962b16cc/index.html
upload: _site/items/3a6d68fc-5a35-4f40-b45d-2268000031a4/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/3a6d68fc-5a35-4f40-b45d-2268000031a4/index.html
upload: _site/items/63501753-9578-4a61-b5a6-7024f5837182/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/63501753-9578-4a61-b5a6-7024f5837182/index.html
upload: _site/items/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/index.html
upload: _site/items/722521b8-22f3-4585-9f2a-a1c24212baef/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/722521b8-22f3-4585-9f2a-a1c24212baef/index.html
upload: _site/legal/cookies/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/cookies/index.html
upload: _site/legal/privacy/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/privacy/index.html
upload: _site/legal/copyright/index.html to s3://add-catalogue-integration.data.bas.ac.uk/legal/copyright/index.html
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-rubric/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-rubric/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-xml/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-xml/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/items/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/index.html
upload: _site/items/d531a142-d6e7-4961-ab36-ab1db39f3f00/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/d531a142-d6e7-4961-ab36-ab1db39f3f00/index.html
upload: _site/items/dd6dd055-481e-4de2-8444-e00d7536f779/index.html to s3://add-catalogue-integration.data.bas.ac.uk/items/dd6dd055-481e-4de2-8444-e00d7536f779/index.html
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-rubric/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-rubric/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-xml/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-xml/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-html/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-html/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-html/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-html/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-rubric/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-rubric/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-rubric/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-rubric/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-xml/2cddeea3-eb67-46af-a002-8251337984d4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2cddeea3-eb67-46af-a002-8251337984d4/iso-xml/2cddeea3-eb67-46af-a002-8251337984d4.xml
upload: _site/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-html/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23/iso-html/2e9b1977-d1a5-4b9b-b58f-cf1a94c63c23.xml
upload: _site/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-xml/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/4149c45d-ce29-49f3-88ed-8366fe1afa23/iso-xml/4149c45d-ce29-49f3-88ed-8366fe1afa23.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-rubric/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-rubric/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-html/33d5a2d4-66d8-46be-82c8-404664b21455.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/33d5a2d4-66d8-46be-82c8-404664b21455/iso-html/33d5a2d4-66d8-46be-82c8-404664b21455.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-xml/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-xml/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-html/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-html/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-rubric/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-rubric/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-html/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-html/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-xml/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/3a6d68fc-5a35-4f40-b45d-2268000031a4/iso-xml/3a6d68fc-5a35-4f40-b45d-2268000031a4.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-xml/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-xml/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-html/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-html/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-rubric/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-rubric/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-xml/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-xml/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-html/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-html/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-html/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-html/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/63501753-9578-4a61-b5a6-7024f5837182/iso-xml/63501753-9578-4a61-b5a6-7024f5837182.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/63501753-9578-4a61-b5a6-7024f5837182/iso-xml/63501753-9578-4a61-b5a6-7024f5837182.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-html/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-html/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-rubric/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-rubric/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-rubric/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda/iso-rubric/6dd2149e-b2e9-40d1-83ce-5d58b9b8dfda.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-html/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-html/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-rubric/722521b8-22f3-4585-9f2a-a1c24212baef.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/722521b8-22f3-4585-9f2a-a1c24212baef/iso-rubric/722521b8-22f3-4585-9f2a-a1c24212baef.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-rubric/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-rubric/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-xml/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-xml/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-rubric/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-rubric/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-xml/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8537f4c6-fc79-4d18-8877-dc2db9ee945e/iso-xml/8537f4c6-fc79-4d18-8877-dc2db9ee945e.xml
upload: _site/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-html/862f7159-9e0d-46e2-9684-df1bf924dabc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/862f7159-9e0d-46e2-9684-df1bf924dabc/iso-html/862f7159-9e0d-46e2-9684-df1bf924dabc.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-rubric/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-rubric/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-rubric/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-rubric/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-html/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-html/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-xml/8643fd87-cca5-4e56-bc81-46af208ef260.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/8643fd87-cca5-4e56-bc81-46af208ef260/iso-xml/8643fd87-cca5-4e56-bc81-46af208ef260.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-rubric/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-rubric/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-rubric/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-rubric/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-xml/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/87cf3067-befd-4a66-8b41-e3b5a60e2140/iso-xml/87cf3067-befd-4a66-8b41-e3b5a60e2140.xml
upload: _site/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-html/9ae21db4-49a9-409c-b48f-af597bbfec17.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/9ae21db4-49a9-409c-b48f-af597bbfec17/iso-html/9ae21db4-49a9-409c-b48f-af597bbfec17.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-html/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-html/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-xml/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/d531a142-d6e7-4961-ab36-ab1db39f3f00/iso-xml/d531a142-d6e7-4961-ab36-ab1db39f3f00.xml
upload: _site/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-xml/c1ed29bc-6136-4467-8357-00d426c8850c.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c1ed29bc-6136-4467-8357-00d426c8850c/iso-xml/c1ed29bc-6136-4467-8357-00d426c8850c.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-html/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-html/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-xml/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-xml/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-xml/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/c920561d-ec14-4e13-a5be-4c7a962b16cc/iso-xml/c920561d-ec14-4e13-a5be-4c7a962b16cc.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-html/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-html/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-rubric/dd6dd055-481e-4de2-8444-e00d7536f779.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/dd6dd055-481e-4de2-8444-e00d7536f779/iso-rubric/dd6dd055-481e-4de2-8444-e00d7536f779.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-rubric/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-rubric/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-html/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-html/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
upload: _site/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-xml/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml to s3://add-catalogue-integration.data.bas.ac.uk/records/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121/iso-xml/f58e3d6c-bc21-40fa-ab1a-a7798c9a8121.xml
Ok. Site published to 'add-catalogue-integration.data.bas.ac.uk'
```

## `version`
  
Show application version.

```
add-metadata-toolbox version
SCAR ADD Metadata Toolbox version: 0.0.0
```
