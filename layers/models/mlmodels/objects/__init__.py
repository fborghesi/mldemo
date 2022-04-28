import tensorflow_hub as hub
import tensorflow as tf
from object_detection.utils import visualization_utils as viz_utils
from six import BytesIO
from PIL import Image
import numpy as np
from object_detection.utils import label_map_util
import os
import logging
from layers.dependencies.python.lib.models import MODELS_DIR

logger = logging.getLogger(__name__)

BASE_DIR = os.path.join(MODELS_DIR, 'objects')
HUB_MODEL_DIR = os.path.join(BASE_DIR, 'tfhub_model')
LABEL_MAP_PATH = os.path.join(BASE_DIR, 'mscoco_label_map.pbtxt')
MIN_SCORE = 0.5

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
with open(os.path.join(HUB_MODEL_DIR, 'url.txt'), 'r') as file:
    url = file.read().rstrip()

# load the model
logger.info("Loading cached model downloaded from URL {}.".format(url))
hub_model = hub.load(HUB_MODEL_DIR)

def load_img(self, src):
    data = BytesIO(tf.io.gfile.GFile(src, 'rb').read())
    img = Image.open(data)
    (w, h) = img.size
    return np.array(img.getdata()).reshape((1, h, w, 3)).astype(np.uint8)


def predict(in_file_path, out_file_path):
    label_id_offset = 0

    # get the image
    logger.info("Loading image from file {0}.".format(in_file_path))
    img_arr = load_img(in_file_path)

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

    logger.info("Writing generated image to file {0}.".format(out_file_path))
    viz_utils.save_image_array_as_png(img_arr[0], out_file_path)
