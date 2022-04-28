import ujson
from lib.validators.login_validator import LoginSchema
from lib.validators.refresh_token_validator import RefreshTokenSchema
from lib.utils.response import Response
from lib.validators.validation_exception import ValidationException
from lib.db.user_helper import UserHelper
from lib.db import mongodb
import logging
import lib.common.log_config

logger = logging.getLogger(__name__)

def user_to_dto(d):
    return {k: v for k, v in d.items() if k != 'password' }

def lambda_handler(event, context):
    validator = LoginSchema()
    user_helper = UserHelper(mongodb)

    try:
        body = ujson.loads(event["body"])
        errors = validator.validate(body)

        if errors:
            raise ValidationException.from_error_dict(errors)

        data = validator.load(body)
        logger.info("Schema: {}".format(str(data)))
        email = data['email']
        token = data['token']

        result = user_helper.get_by_email(email)
        result["token"] = token

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
