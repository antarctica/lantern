// noinspection NpmUsedModulesInstalled,JSUnresolvedFunction
const AWS = require('aws-sdk');

// noinspection JSUnresolvedFunction
const s3 = new AWS.S3();

// noinspection JSUnresolvedVariable
const environment_name = process.env.ENVIRONMENT_NAME;

// noinspection JSUnresolvedVariable
const s3_bucket = process.env.S3_BUCKET;

const s3_object = "lookups.json";

// noinspection JSUnresolvedVariable,JSUnusedLocalSymbols
exports.handler_read = async (event, context) => {
  if (event['requestContext']['http']['method'].toLowerCase() !== 'get') {
    return {
      statusCode: 405
    };
  }

  const artefact_lookup_id = getArtefactLookupId(event);

  const artefact_lookups = await getArtefactLookups();
  const artefact_lookup = getArtefactLookup(artefact_lookup_id, artefact_lookups['artefacts']);
  if (!artefact_lookup) {
    return {
      statusCode: 404,
      body: "404 - File not found.",
      headers: {
        'Environment': environment_name
      }
    };
  }

  const origin_uri = getOriginUri(artefact_lookup);
  if (!origin_uri) {
    return {
      statusCode: 500,
      body: "500 - Error generating download. Please contact servicedesk@bas.ac.uk for support.",
      headers: {
        'Environment': environment_name
      }
    };
  }

  return {
    statusCode: 302,
    headers: {
      'Environment': environment_name,
      'Location': origin_uri
    }
  };
};

// noinspection JSUnresolvedVariable,JSUnusedLocalSymbols
exports.handler_write = async (event) => {
  if (event['requestContext']['http']['method'].toLowerCase() !== 'post') {
    return {
      statusCode: 405
    };
  }

  const artefact_lookup = generateArtefactLookup(event);
  const artefact_lookups = await getArtefactLookups();

  if (getArtefactLookup(artefact_lookup['artefact_id'], artefact_lookups['artefacts'])) {
    console.warn(`Lookup item with ID '${artefact_lookup['artefact_id']}' already exists`)
    return {
      statusCode: 409,
      headers: {
        'Environment': environment_name
      }
    };
  }

  artefact_lookups['artefacts'][artefact_lookup['artefact_id']] = artefact_lookup;
  await putArtefactLookups(artefact_lookups);

  return {
    statusCode: 204,
    headers: {
      'Environment': environment_name
    }
  };
};

function getArtefactLookupId(event) {
  try {
    const artefact_lookup_id = event['rawPath'].split('/').pop();
    console.log(`Artefact lookup ID: '${artefact_lookup_id}'`);
    return artefact_lookup_id;
  } catch (error) {
    console.error('Could not determine artefact lookup ID from URL path');
    console.log(`event rawPath: ${event['rawPath']}`)
  }
}

async function getArtefactLookups() {
  console.log(`S3 bucket: ${s3_bucket} S3 object: ${s3_object}`)

  // noinspection JSUnresolvedFunction
  const lookup_file = await s3.getObject({Bucket: s3_bucket, Key: s3_object}).promise();

  // noinspection JSUnresolvedVariable,JSCheckFunctionSignatures
  return JSON.parse(lookup_file.Body.toString('utf-8'));
}

function getArtefactLookup(artefact_lookup_id, artefact_lookups) {
  if (!(artefact_lookup_id in artefact_lookups)) {
    console.warn("Lookup item not found");
    return false
  }

  return artefact_lookups[artefact_lookup_id];
}

function getOriginUri(artefact_lookup) {
  try {
    const origin_uri = artefact_lookup['origin_uri'];
    console.log(`Origin URI: ${origin_uri}`);
    return origin_uri;
  } catch (error) {
    console.error('Lookup item missing origin URI');
    return false;
  }
}

function generateArtefactLookup(event) {
  const artefact_lookup = JSON.parse(event['body']);

  // noinspection JSUnusedLocalSymbols
  const artefact_id = artefact_lookup['artefact_id'];

  const artefact_lookups = {
    "$id": "#",
    "$schema": "https://metadata-standards.data.bas.ac.uk/scar-add-metadata-toolbox-downloads-proxy-schemas/v1/artefact-lookups-v1.json",
    "artefacts": {
      artefact_id: artefact_lookup
    }
  };

  validateLookups(artefact_lookups);

  return artefact_lookup;
}

async function putArtefactLookups(lookups) {
  validateLookups(lookups);

  // noinspection JSUnresolvedFunction
  await s3.putObject({Bucket: s3_bucket, Key: s3_object, Body: JSON.stringify(lookups)}).promise();
}

function validateLookups(lookups) {
  // TODO: raise exception if lookups not validate against JSON Schema.
}
