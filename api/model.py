import tensorflow as tf
import tensorflow_hub as hub
from six import BytesIO
from PIL import Image
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
import numpy as np
import logging

logger = logging.getLogger(__name__)

tf.get_logger().setLevel('ERROR')

LABEL_MAP = 'api/mscoco_label_map.pbtxt'

ALL_MODELS = {
    'CenterNet HourGlass104 512x512': 'https://tfhub.dev/tensorflow/centernet/hourglass_512x512/1',
    'CenterNet HourGlass104 Keypoints 512x512': 'https://tfhub.dev/tensorflow/centernet/hourglass_512x512_kpts/1',
    'CenterNet HourGlass104 1024x1024': 'https://tfhub.dev/tensorflow/centernet/hourglass_1024x1024/1',
    'CenterNet HourGlass104 Keypoints 1024x1024': 'https://tfhub.dev/tensorflow/centernet/hourglass_1024x1024_kpts/1',
    'CenterNet Resnet50 V1 FPN 512x512': 'https://tfhub.dev/tensorflow/centernet/resnet50v1_fpn_512x512/1',
    'CenterNet Resnet50 V1 FPN Keypoints 512x512': 'https://tfhub.dev/tensorflow/centernet/resnet50v1_fpn_512x512_kpts/1',
    'CenterNet Resnet101 V1 FPN 512x512': 'https://tfhub.dev/tensorflow/centernet/resnet101v1_fpn_512x512/1',
    'CenterNet Resnet50 V2 512x512': 'https://tfhub.dev/tensorflow/centernet/resnet50v2_512x512/1',
    'CenterNet Resnet50 V2 Keypoints 512x512': 'https://tfhub.dev/tensorflow/centernet/resnet50v2_512x512_kpts/1',
    'EfficientDet D0 512x512': 'https://tfhub.dev/tensorflow/efficientdet/d0/1',
    'EfficientDet D1 640x640': 'https://tfhub.dev/tensorflow/efficientdet/d1/1',
    'EfficientDet D2 768x768': 'https://tfhub.dev/tensorflow/efficientdet/d2/1',
    'EfficientDet D3 896x896': 'https://tfhub.dev/tensorflow/efficientdet/d3/1',
    'EfficientDet D4 1024x1024': 'https://tfhub.dev/tensorflow/efficientdet/d4/1',
    'EfficientDet D5 1280x1280': 'https://tfhub.dev/tensorflow/efficientdet/d5/1',
    'EfficientDet D6 1280x1280': 'https://tfhub.dev/tensorflow/efficientdet/d6/1',
    'EfficientDet D7 1536x1536': 'https://tfhub.dev/tensorflow/efficientdet/d7/1',
    'SSD MobileNet v2 320x320': 'https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2',
    'SSD MobileNet V1 FPN 640x640': 'https://tfhub.dev/tensorflow/ssd_mobilenet_v1/fpn_640x640/1',
    'SSD MobileNet V2 FPNLite 320x320': 'https://tfhub.dev/tensorflow/ssd_mobilenet_v2/fpnlite_320x320/1',
    'SSD MobileNet V2 FPNLite 640x640': 'https://tfhub.dev/tensorflow/ssd_mobilenet_v2/fpnlite_640x640/1',
    'SSD ResNet50 V1 FPN 640x640 (RetinaNet50)': 'https://tfhub.dev/tensorflow/retinanet/resnet50_v1_fpn_640x640/1',
    'SSD ResNet50 V1 FPN 1024x1024 (RetinaNet50)': 'https://tfhub.dev/tensorflow/retinanet/resnet50_v1_fpn_1024x1024/1',
    'SSD ResNet101 V1 FPN 640x640 (RetinaNet101)': 'https://tfhub.dev/tensorflow/retinanet/resnet101_v1_fpn_640x640/1',
    'SSD ResNet101 V1 FPN 1024x1024 (RetinaNet101)': 'https://tfhub.dev/tensorflow/retinanet/resnet101_v1_fpn_1024x1024/1',
    'SSD ResNet152 V1 FPN 640x640 (RetinaNet152)': 'https://tfhub.dev/tensorflow/retinanet/resnet152_v1_fpn_640x640/1',
    'SSD ResNet152 V1 FPN 1024x1024 (RetinaNet152)': 'https://tfhub.dev/tensorflow/retinanet/resnet152_v1_fpn_1024x1024/1',
    'Faster R-CNN ResNet50 V1 640x640': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet50_v1_640x640/1',
    'Faster R-CNN ResNet50 V1 1024x1024': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet50_v1_1024x1024/1',
    'Faster R-CNN ResNet50 V1 800x1333': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet50_v1_800x1333/1',
    'Faster R-CNN ResNet101 V1 640x640': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet101_v1_640x640/1',
    'Faster R-CNN ResNet101 V1 1024x1024': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet101_v1_1024x1024/1',
    'Faster R-CNN ResNet101 V1 800x1333': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet101_v1_800x1333/1',
    'Faster R-CNN ResNet152 V1 640x640': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet152_v1_640x640/1',
    'Faster R-CNN ResNet152 V1 1024x1024': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet152_v1_1024x1024/1',
    'Faster R-CNN ResNet152 V1 800x1333': 'https://tfhub.dev/tensorflow/faster_rcnn/resnet152_v1_800x1333/1',
    'Faster R-CNN Inception ResNet V2 640x640': 'https://tfhub.dev/tensorflow/faster_rcnn/inception_resnet_v2_640x640/1',
    'Faster R-CNN Inception ResNet V2 1024x1024': 'https://tfhub.dev/tensorflow/faster_rcnn/inception_resnet_v2_1024x1024/1',
    'Mask R-CNN Inception ResNet V2 1024x1024': 'https://tfhub.dev/tensorflow/mask_rcnn/inception_resnet_v2_1024x1024/1'
}

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

MODEL_NAME = 'Faster R-CNN ResNet50 V1 640x640'
logger.info("Loading model {0} from URL {1}.".format(MODEL_NAME, ALL_MODELS[MODEL_NAME]))
hub_model = hub.load(ALL_MODELS[MODEL_NAME])

class Model:
    def __init__(self):
        logger.info("Loading labels from {0}.".format(LABEL_MAP))
        self._category_index = label_map_util.create_category_index_from_labelmap(LABEL_MAP, use_display_name=True)

    def _load_img(self, src):
        data = BytesIO(tf.io.gfile.GFile(src, 'rb').read())
        img = Image.open(data)
        (w, h) = img.size
        return np.array(img.getdata()).reshape((1, h, w, 3)).astype(np.uint8)


    def process(self, in_filename, out_filename, min_score=0.5):
        label_id_offset = 0

        # get the image
        logger.info("Loading image from file {0}.".format(in_filename))
        img_arr = self._load_img(in_filename)

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
              self._category_index,
              use_normalized_coordinates=True,
              max_boxes_to_draw=200,
              min_score_thresh=min_score,
              agnostic_mode=False,
              keypoints=keypoints,
              keypoint_scores=keypoint_scores,
              keypoint_edges=COCO17_HUMAN_POSE_KEYPOINTS)

        logger.info("Writing generated image to file {0}.".format(out_filename))
        viz_utils.save_image_array_as_png(img_arr[0], out_filename)