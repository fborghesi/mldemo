import os
from io import BytesIO

from lib.aws.secret_mgr_helper import SecretsManagerHelper
from lib.utils.response import Response
import base64
import logging
import lib.common.log_config
import openai


logger = logging.getLogger(__name__)

# get the open ai api key
LAMBDA_ENVIRONMENT = os.environ['LAMBDA_ENVIRONMENT']
OPENAI_API_KEY = '{env}.OpenAIApiKey'.format(env=LAMBDA_ENVIRONMENT)
secrets_helper = SecretsManagerHelper()
secret = secrets_helper.get_secret(OPENAI_API_KEY)

assert secret is not None, 'Could not retrieve OpenAI API Key "{secret}!"'.format(secret=OPENAI_API_KEY)
openai.api_key = secret['api_key']

def lambda_handler(event, context):
    try:
        body = event['body']
        audio = base64.b64decode(body)

        buffer = BytesIO(audio)
        buffer.name = "input.mp3"

        result = openai.Audio.transcribe("whisper-1", buffer)
        return Response.success(200, result).to_json()

    except Exception as e:
        logger.exception(e)

        return Response.failure(400, str(e)).to_json()
