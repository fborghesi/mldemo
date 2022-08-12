import base64

import ujson
from lib.validators.login_validator import LoginSchema
from lib.validators.refresh_token_validator import RefreshTokenSchema
from lib.utils.response import Response
from lib.validators.validation_exception import ValidationException
from lib.db.user_helper import UserHelper
from lib.db import mongodb
import logging
from oauth2client import client
from lib.validators import token
from lib.aws.secret_mgr_helper import SecretsManagerHelper
import os

logger = logging.getLogger(__name__)

CLIENT_SECRET_JSON = "/var/task/lib/validators/client_secret.json"
LAMBDA_ENVIRONMENT = os.environ['LAMBDA_ENVIRONMENT']
GOOGLE_AUTH_REDIRECT_URL = os.environ['GOOGLE_AUTH_REDIRECT_URL']
GOOGLE_AUTH_SECRET_NAME = '{env}.GoogleAuthSecret'.format(env=LAMBDA_ENVIRONMENT)
secret_mgr_helper = SecretsManagerHelper()
google_auth_secret = secret_mgr_helper.get_secret(GOOGLE_AUTH_SECRET_NAME)

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
];


def get_credentials_from_google(auth_code, redirect_uri):
    client_config = ujson.load(open(CLIENT_SECRET_JSON, 'r'))['web']

    # redirect_uris = client_config["redirect_uris"]
    # redirect_uri = redirect_uris[0 if LAMBDA_ENVIRONMENT == "dev" else 1]
    logger.info("Getting credentials for code {auth_code}, redirect URI: {uri}".format(auth_code=auth_code, uri=redirect_uri))

    credentials = client.credentials_from_code(
        client_config["client_id"],
        google_auth_secret["client_secret"],
        SCOPES,
        auth_code,
        redirect_uri=redirect_uri
    )

    logger.info(
        "User information for code {code}: {user_info}".format(code=auth_code, user_info=str(credentials.id_token)))

    # get field data from credentials
    return credentials.id_token


def user_to_dto(d):
    return {k: v for k, v in d.items() if k != 'password' }

def local_login(body, user_helper):
    validator = LoginSchema()

    try:
        errors = validator.validate(body)

        if errors:
            raise ValidationException.from_error_dict(errors)

        data = validator.load(body)
        logger.info("Schema: {}".format(str(data)))

        result = user_helper.get_by_email(data['email'])
        result["token"] = data['token']

        return Response.success(200, result)
    except ValidationException as e:
        logger.exception(e)
        return Response.failure(400, "Errors found: {errors}".format(errors=errors))


def google_login(code, redirect_uri, user_helper):
    data = get_credentials_from_google(code, redirect_uri)

    # find and update user in db
    found = user_helper.get_by_email(data['email'])

    if found:
        logger.info("User found in database: {found}".format(found=found))
    else:
        # create user with pending activation
        dto = {'first_name': data["given_name"], 'last_name': data["family_name"], 'email': data["email"],
               'is_admin': False,
               'is_active': False}
        id = user_helper.create(dto)
        found = user_helper.get_by_id(id)

    if not found["is_active"]:
        return Response.redirect("{uri}?noaccess=1".format(uri=GOOGLE_AUTH_REDIRECT_URL));
        # raise Exception("Your account has not yet been approved by Administrators.")

    found["first_name"] = data["given_name"]
    found["last_name"] = data["family_name"]
    found["email"] = data["email"]
    logger.info("Updating user with data: ", found)

    user_helper.update(found["id"], found)

    result = found
    result["token"] = token.create_access_token(found)
    #params = urllib.parse.urlencode(result)
    data = ujson.dumps(result)
    b64_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
    params = 'data={}'.format(b64_data)
    uri = "{redirect_url}?{params}".format(redirect_url=GOOGLE_AUTH_REDIRECT_URL,
                                           params=params)
    logger.info("Redirect URI: {}".format(uri))
    return Response.redirect(uri)


def lambda_handler(event, context):
    user_helper = UserHelper(mongodb)

    try:
        if event["httpMethod"] == "POST":
            body = ujson.loads(event["body"])
            response = local_login(body, user_helper)
        else:
            context = event["requestContext"]
            domain_name = context["domainName"]
            path = context["path"]
            proto = 'http' + 's' if ('localhost' not in domain_name) else ''
            redirect_uri = '{proto}://{domain_name}{path}'.format(proto=proto, domain_name=domain_name, path=path)

            params = event["queryStringParameters"]
            response = google_login(params['code'], redirect_uri, user_helper)
    except Exception as e:
        logger.exception(e)
        return Response.failure(400, str(e))

    return response.to_json()

def token_refresh(event, context):
    validator = RefreshTokenSchema()

    try:
        body = ujson.loads(event["body"])
        errors = validator.validate(body)

        if errors:
            raise ValidationException.from_error_dict(errors)

        result = user_to_dto(validator.load(body))
        return Response.success(200, result).to_json()
    except Exception as e:
        logger.exception('User login failed: {msg}'.format(msg=str(e)))
        return Response.failure(400, str(e)).to_json()
