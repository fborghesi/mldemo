from lib.utils.response import Response
from keras.preprocessing.image import img_to_array
from keras.models import model_from_json
import numpy as np
import os
from PIL import Image
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

BASE_DIR = '/opt/mlmodels/cars'
IMAGE_RESIZE_W = IMAGE_RESIZE_H = 150

model = None
with open(os.path.join(BASE_DIR, 'model.json'), 'r') as json_file:
    model_json = json_file.read()
    model = model_from_json(model_json)
    model.load_weights(os.path.join(BASE_DIR, 'weights.h5'))


def resize_img(img_data):
    image = Image.open(BytesIO(img_data))
    if image.mode != "RGB":
        image = image.convert("RGB")

    return image.resize((IMAGE_RESIZE_W, IMAGE_RESIZE_H))


def img_to_model_input(image):
    arr = img_to_array(image)
    arr = np.expand_dims(image, axis=0)
    arr = arr.astype('float32') / 255
    return arr


def predict(img):
    class_labels = ['front', 'right', 'left', 'back', 'wheel']

    # img = load_image(in_img_path)
    img_array = img_to_model_input(img)

    y_pred = model.predict(img_array, batch_size=None, verbose=0, steps=None)
    max_score = np.argmax(y_pred, axis=1)[0]
    img_class = class_labels[max_score]

    logger.info('Prediction: {}; Class: {}'.format(y_pred, img_class))

    return img_class

def lambda_handler(event, context):
    try:
        body = base64.b64decode(event['body'])

        image = resize_img(body)

        # do prediction
        result = predict(image)

        return Response.success(200, result).to_json()

    except Exception as e:
        logger.exception(e)

        return Response.failure(400, str(e)).to_json()
