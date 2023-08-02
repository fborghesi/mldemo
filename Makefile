PROFILE=franco.borghesi@gmail.com
REGION=us-east-1
ACCOUNT_ID=491431825058
REGISTRY=$(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
IMG_NAME=mldemo
IMG_TAG_MODEL=model-base
IMG_TAG_PYTHON=python-base

all: python-base model-base

login:
	aws ecr --profile $(PROFILE) get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REGISTRY)

python-base: login
	docker build -t $(IMG_TAG_PYTHON):latest -f api/Dockerfile-python-base .
	docker tag $(IMG_TAG_PYTHON):latest $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_PYTHON)-latest
	docker push $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_PYTHON)-latest

model-base: login python-base
	docker build -t $(IMG_TAG_MODEL):latest -f api/Dockerfile-model-base .
	docker tag $(IMG_TAG_MODEL):latest $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_MODEL)-latest
	docker push $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_MODEL)-latest
