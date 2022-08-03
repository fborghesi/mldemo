from lib.utils.response import Response
import tensorflow_hub as hub
import tensorflow as tf
from object_detection.utils import visualization_utils as viz_utils
from object_detection.utils import label_map_util
from six import BytesIO
from PIL import Image
import numpy as np
import base64
import os
import shutil
import time
import tarfile
import logging
import lib.common.log_config

BASE_DIR = '/opt/mlmodels/objects'
URL_FILE_NAME = os.path.join(BASE_DIR, 'tfhub_model', 'url.txt')
HUB_MODEL_SRC_TAR_FILE = os.path.join(BASE_DIR, 'tfhub_model', '1.tar.gz')
HUB_MODEL_DIR_TGT = '/tmp/tfhub_model'
HUB_MODEL_DIR_LOCK = HUB_MODEL_DIR_TGT + '.lock'
LABEL_MAP_PATH = os.path.join(BASE_DIR, 'mscoco_label_map.pbtxt')
MIME_TYPE = 'image/png'
MIN_SCORE = 0.5
logger = logging.getLogger(__name__)


def target_exists():
    return os.path.isdir(HUB_MODEL_DIR_TGT)


def lock_exists():
    return os.path.isdir(HUB_MODEL_DIR_LOCK)


def wait_on_lock():
    count = 0
    if lock_exists():
        while not target_exists() and count < 60:
            time.sleep(1)
            count += 1

    return target_exists()


def extract_model_lock():
    logger.info(
        "Extracting tensorflow model from {src} into lock dir {tgt}.".format(src=HUB_MODEL_SRC_TAR_FILE, tgt=HUB_MODEL_DIR_LOCK))
    if not lock_exists():
        os.mkdir(HUB_MODEL_DIR_LOCK)
    tar = tarfile.open(HUB_MODEL_SRC_TAR_FILE, "r:gz")
    tar.extractall(HUB_MODEL_DIR_LOCK)
    tar.close()


def rename_lock():
    if not target_exists():
        logger.info("Moving tensorflow model from lock dir {src} to {tgt}.".format(src=HUB_MODEL_DIR_LOCK,
                                                                                   tgt=HUB_MODEL_DIR_TGT))
        shutil.move(HUB_MODEL_DIR_LOCK, HUB_MODEL_DIR_TGT)


# model does not exist in /tmp?
if not target_exists():
    logger.info("Target directory {tgt} not found.".format(tgt=HUB_MODEL_DIR_TGT))

    # copy model if no copy in progress, or wait for it to finish otherwise
    if not lock_exists() or not wait_on_lock():
        extract_model_lock()
        rename_lock()

# load class labels
logger.info("Loading labels from {}.".format(LABEL_MAP_PATH))
class_labels = label_map_util.create_category_index_from_labelmap(LABEL_MAP_PATH, use_display_name=True)

COCO17_HUMAN_POSE_KEYPOINTS = [(0, 1),
                               (0, 2),
                               (1, 3),
                               (2, 4),
                               (0, 5),
                               (0, 6),
                               (5, 7),
                               (7, 9),
                               (6, 8),
                               (8, 10),
                               (5, 6),
                               (5, 11),
                               (6, 12),
                               (11, 12),
                               (11, 13),
                               (13, 15),
                               (12, 14),
                               (14, 16)]


# be sure you run <b>make</b> on current directory to install desired model
with open(URL_FILE_NAME, 'r') as file:
    url = file.read().rstrip()

# load the model
logger.info("Loading cached model downloaded from URL {} from {}.".format(url, HUB_MODEL_DIR_TGT))
load_options = tf.saved_model.LoadOptions(experimental_io_device='/job:localhost')
hub_model = hub.load(HUB_MODEL_DIR_TGT, options=load_options)

def load_img(self, src):
    data = BytesIO(tf.io.gfile.GFile(src, 'rb').read())
    img = Image.open(data)
    (w, h) = img.size
    return np.array(img.getdata()).reshape((1, h, w, 3)).astype(np.uint8)


def predict(img_data):
    label_id_offset = 0

    # resize the image
    img = Image.open(BytesIO(img_data))
    (w, h) = img.size
    img_arr = np.array(img.getdata()).reshape((1, h, w, 3)).astype(np.uint8)

    # predict
    logger.info("Passing image numpy array to model for prediction.")
    results = hub_model(img_arr)

    # convert predicted dict values to numpy arrays
    result = {key: value.numpy() for key, value in results.items()}

    # check if keypoints are available
    keypoints, keypoint_scores = None, None
    if 'detection_keypoints' in result:
        keypoints = result['detection_keypoints'][0]
        keypoint_scores = result['detection_keypoint_scores'][0]

    # draw on image
    logger.info("Generating output image in memory.")
    viz_utils.visualize_boxes_and_labels_on_image_array(
          img_arr[0],
          result['detection_boxes'][0],
          (result['detection_classes'][0] + label_id_offset).astype(int),
          result['detection_scores'][0],
          class_labels,
          use_normalized_coordinates=True,
          max_boxes_to_draw=200,
          min_score_thresh=MIN_SCORE,
          agnostic_mode=False,
          keypoints=keypoints,
          keypoint_scores=keypoint_scores,
          keypoint_edges=COCO17_HUMAN_POSE_KEYPOINTS)

    return img_arr[0]


def lambda_handler(event, context):
    try:
        body = event['body']
        body_data = base64.b64decode(body)

        # do prediction
        prediction = predict(body_data)

        # set up response
        result = base64.b64encode(prediction)
        return Response.success(200, result, MIME_TYPE, True).to_json()
    except Exception as e:
        logger.exception(e)

        return Response.failure(400, str(e)).to_json()
