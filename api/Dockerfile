FROM public.ecr.aws/lambda/python:3.8

#protobuf-compiler
RUN yum install -y git wget unzip gcc

RUN mkdir -p /tmp/installs/protoc_3.3.0 && \
    cd /tmp/installs/protoc_3.3.0 && \
    wget https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip && \
    unzip protoc-3.3.0-linux-x86_64.zip

RUN git clone --depth 1 https://github.com/tensorflow/models && \
    cd models/research/ && \
    /tmp/installs/protoc_3.3.0/bin/protoc object_detection/protos/*.proto --python_out=. && \
    cp object_detection/packages/tf2/setup.py . && \
    python -m pip install . && \
    rm -rf /tmp/installs/protoc_3.3.0

COPY requirements.txt ./
RUN python -m pip install wheel && python -m pip install -r requirements.txt -t .


RUN mkdir api/
COPY * api/
#COPY app.py model.py mscoco_label_map.pbtxt ./

# Command can be overwritten by providing a different command in the template directly.
CMD ["api.app.lambda_handler"]
