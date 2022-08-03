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
from lib.db.db_helper_exception import DatabaseHelperException
from lib.aws.secret_mgr_helper import SecretsManagerHelper
import urllib.parse
import os
import lib.common.log_config

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

def auth_google(auth_code):
    client_config = ujson.load(open(CLIENT_SECRET_JSON, 'r'))['web']

    try:
        logger.info("Getting credentials for code {auth_code}".format(auth_code=auth_code))

        redirect_uri = client_config["redirect_uris"][0]
        credentials = client.credentials_from_code(client_config["client_id"], google_auth_secret["client_secret"], SCOPES, auth_code,
            redirect_uri=redirect_uri)
        #redirect_uri='postmessage'

        logger.info(
            "User information for code {code}: {user_info}".format(code=auth_code, user_info=str(credentials.id_token)))

        # get field data from credentials
        return credentials.id_token

    except client.FlowExchangeError as e:
        logger.exception(e)
        raise ValidationException(str(e))



def user_to_dto(d):
    return {k: v for k, v in d.items() if k != 'password' }

def lambda_handler(event, context):
    validator = LoginSchema()
    user_helper = UserHelper(mongodb)

    try:
        if event["httpMethod"] == "POST":
            body = ujson.loads(event["body"])
            errors = validator.validate(body)

            if errors:
                raise ValidationException.from_error_dict(errors)

            data = validator.load(body)
            logger.info("Schema: {}".format(str(data)))

            result = user_helper.get_by_email(data['email'])
            result["token"] = data['token']
        else:
            query_string = event["queryStringParameters"]
            data = auth_google(query_string['code'])

            try:
                # find and update user in db
                found = user_helper.get_by_email(data['email'])
                logger.info("User found in database: {found}".format(found=found))

                if not found["is_active"]:
                    raise ValidationException("Your account is pending approval from Administrators.")

                found["first_name"] = data["given_name"]
                found["last_name"] = data["family_name"]
                found["email"] = data["email"]
                logger.info("Updating user with data: ", found)

                user_helper.update(found["id"], found)

                result = found
                result["token"] = token.create_access_token(found)
                uri = "{redirect_url}?{params}".format(redirect_url=GOOGLE_AUTH_REDIRECT_URL, params=urllib.parse.urlencode(result))
                return Response.redirect(uri).to_json()

            except DatabaseHelperException as e:
                # track user for the future
                dto = {'first_name': data["given_name"], 'last_name': data["family_name"], 'email': data["email"], 'is_admin': False,
                       'is_active': False}
                user_helper.create(dto)
                raise ValidationException(str(e))

        return Response.success(200, result).to_json()
    except ValidationException as e:
        logger.exception(e)
        return Response.failure(400, "Errors found: {errors}".format(errors=errors)).to_json()
    except Exception as e:
        logger.exception(e)
        return Response.failure(400, str(e)).to_json()


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
