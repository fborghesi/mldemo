import ujson
from lib.db.user_helper import UserHelper
from lib.db.db_helper_exception import DatabaseHelperException
from lib.validators.user_validator import UserRegistrationSchema
from lib.validators.validation_exception import ValidationException
from lib.utils.response import Response
from lib.db import mongodb
import os
import logging

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    user_helper = UserHelper(mongodb)
    validator = UserRegistrationSchema()

    try:
        if 'pathParameters' in event and 'Id' in event["pathParameters"]:
            id = str(event['pathParameters']['Id'])
            body = ujson.loads(event['body'])
            errors = validator.validate(body)

            if errors:
                raise ValidationException.from_error_dict(errors)

            user_helper.update(id, body)

            return Response.success(204, None).to_json()

        raise ValueError("Invalid Id or Id not set.")

    except DatabaseHelperException as e:
        logger.exception('User update failed: {msg}'.format(msg=str(e)))
        return Response.failure(code=404, msg=str(e)).to_json()
    except Exception as e:
        logger.exception('User update failed: {msg}'.format(msg=str(e)))
        return Response.failure(code=400, msg=str(e)).to_json()


