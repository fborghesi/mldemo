from lib.db.user_helper import UserHelper
from lib.db.db_helper_exception import DatabaseHelperException
from lib.utils.response import Response
from lib.db import mongodb
import logging

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    user_helper = UserHelper(mongodb)

    try:
        if 'pathParameters' in event and 'Id' in event["pathParameters"]:
            id = str(event['pathParameters']['Id'])
            user_helper.delete(id)
            return Response.success(204, None).to_json()

        raise ValueError("Invalid Id or Id not set.")

    except DatabaseHelperException as e:
        logger.exception('User deletion failed: {msg}'.format(msg=str(e)))
        return Response.failure(code=404, msg=str(e)).to_json()
    except Exception as e:
        logger.exception('User deletion failed: {msg}'.format(msg=str(e)))
        return Response.failure(code=400, msg=str(e)).to_json()