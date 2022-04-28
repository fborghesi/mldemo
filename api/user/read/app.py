from lib.db.user_helper import UserHelper
from lib.utils.response import Response
from lib.db import mongodb
import logging

logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    user_helper = UserHelper(mongodb)

    # jwt = event['headers']['Authorization']
    # data = jwt.decode(auth_token, os.environ['SECRET_KEY'], algorithms=["HS256"])
    # id, first_name, last_name = (data['id'], data['first_name']], data['last_name'])

    try:
        if 'pathParameters' not in event or event['pathParameters'] is None or 'Id' not in event["pathParameters"]:
            found = user_helper.get_all()
            return Response.success(200, found).to_json()
        else:
            id = str(event['pathParameters']['Id'])
            user = user_helper.get_by_id(id)
            return Response.success(200, user).to_json()

    except BaseException as e:
        logger.exception('User list failed: {msg}'.format(msg=str(e)))
        return Response.failure(code=404, msg=str(e)).to_json()
