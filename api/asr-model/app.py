from lib.utils.response import Response
from keras.preprocessing.image import img_to_array
from keras.models import model_from_json
import numpy as np
import os
from PIL import Image
import base64
from io import BytesIO
import logging
import lib.common.log_config
import openai

logger = logging.getLogger(__name__)

# get the open ai api key
OPENAI_API_KEY = '{env}.OpenAIApiKey'.format(env=LAMBDA_ENVIRONMENT)
secrets_helper = SecretsManagerHelper()
secret = secrets_helper.get_secret(OPENAI_API_KEY)
assert secret is not None, 'Could not retrieve OpenAI API Key "{secret}!"'.format(secret=OPENAI_API_KEY)

openai.api_key = secret['key']

def lambda_handler(event, context):
    try:
        body = event['body']
        audio = base64.b64decode(body)
        result = openai.Audio.transcribe("Whisper-1", body)
        return Response.success(200, result).to_json()

    except Exception as e:
        logger.exception(e)

        return Response.failure(400, str(e)).to_json()
