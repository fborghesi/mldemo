import boto3
import os
from pathlib import Path
import ntpath
from .model import Model
import tempfile
import logging

OUT_DIR = 'out/'
logger = logging.getLogger(__name__)
s3 = boto3.client('s3')
model = Model()


def lambda_handler(event, context):
    in_file_name = out_file_name = None

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        object_size = record['s3']['object']['size']

        base_file_name = tempfile.mkstemp(prefix='img_')[1]
        in_file_name = base_file_name + '_in' + os.path.splitext(object_key)[1]
        out_file_name = base_file_name + '_out.png'

        try:
            # download input file from bucket
            logger.info('Downloading {0} bytes from s3://{1}/{2} into local temporary file {3}.'.format(object_size, bucket_name, object_key, in_file_name))
            s3.download_file(bucket_name, object_key, in_file_name)

            # do prediction
            model.process(in_file_name, out_file_name)

            # upload output file to bucket
            upload_object_key = OUT_DIR + os.path.splitext(ntpath.basename(object_key))[0] + ".png"
            logger.info('Uploading file from {0} to s3://{1}/{2}.'.format(out_file_name, bucket_name, upload_object_key))
            s3.upload_file(out_file_name, bucket_name, upload_object_key)

        finally:
            Path(in_file_name).unlink(missing_ok=True)
            Path(out_file_name).unlink(missing_ok=True)

