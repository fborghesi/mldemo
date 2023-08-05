ENV?=dev
ENVFILE=.env-$(ENV)

# load the environment file
include $(ENVFILE)
export $(shell sed '/^\#/d; s/=.*//' $(ENVFILE))

PROFILE=franco.borghesi@gmail.com
REGION=us-east-1
ACCOUNT_ID=491431825058
REGISTRY=$(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
IMG_NAME=mldemo
IMG_TAG_MODEL=model-base
IMG_TAG_PYTHON=python-base

DEPLOY_BUCKET=mldemo-deploy-bucket
STACK_NAME=mldemo-tech-$(ENV)
API_DIR=.

all: deploy
images: python-base model-base

login:
	aws ecr --profile $(PROFILE) get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REGISTRY)

python-base: login
	echo "> > > Building Python Base Image < < <"
	docker build -t $(IMG_TAG_PYTHON):latest -f api/Dockerfile-python-base .
	docker tag $(IMG_TAG_PYTHON):latest $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_PYTHON)-latest
	docker push $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_PYTHON)-latest

model-base: login python-base
	echo "> > > Building ML Model Base Image < < <"
	docker build -t $(IMG_TAG_MODEL):latest -f api/Dockerfile-model-base .
	docker tag $(IMG_TAG_MODEL):latest $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_MODEL)-latest
	docker push $(REGISTRY)/$(IMG_NAME):$(IMG_TAG_MODEL)-latest

build:
	echo "> > > Building AWS Template < < <"
	sam build \
		--template $(API_DIR)/template.yaml \
		--build-dir $(API_DIR)/.aws-sam/build \
		--use-container

package: build
	echo "> > > Building docker images for lambda functions < < <"
	sam package \
		--template-file $(API_DIR)/.aws-sam/build/template.yaml \
		--output-template-file $(API_DIR)/.aws-sam/build/packaged-template.yaml \
		--s3-bucket mldemo-data-upload-bucket \
		--image-repository $(REGISTRY)/mldemo \
		--profile=$(PROFILE)

deploy: package
	@echo "> > > Deploying to AWS < < <"
	@echo "   Environment: $(ENV)"
	@echo ""
	sam deploy deploy \
	  --template-file $(API_DIR)/.aws-sam/build/template.yaml \
	  --stack-name $(STACK_NAME) \
	  --s3-bucket $(DEPLOY_BUCKET) \
	  --image-repository $(REGISTRY)/mldemo \
	  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
	  --profile=$(PROFILE) \
	  --parameter-overrides \
	  \"LambdaEnvironment\"=\"$(ENV)\" \
	  \"DatabaseHost\"=\$(DatabaseHost)\" \
	  \"DatabasePort\"=\"$(DatabasePort)\" \
	  \"DatabaseUser\"=\"$(DatabaseUser)\" \
	  \"DatabasePassword\"=\"$(DatabasePassword)\" \
	  \"DatabaseName\"=\"$(DatabaseName)\" \
	  \"CorsAllowedHeaders\"=\"$(CorsAllowedHeaders)\" \
	  \"CorsAllowedOrigin\"=\"$(CorsAllowedOrigin)\" \
	  \"CorsAllowedMethods\"=\"$(CorsAllowedMethods)\" \
	  \"SessionTimeoutMins\"=\"$(SessionTimeoutMins)\" \
	  \"GoogleAuthClientSecret\"=\"$(GoogleAuthClientSecret)\" \
	  \"GoogleAuthRedirectDevUrl\"=\"$(GoogleAuthRedirectDevUrl)\" \
	  \"GoogleAuthRedirectProdUrl\"=\"$(GoogleAuthRedirectProdUrl)\" \
	  \"OpenAIApiKey\"=\"$(OpenAIApiKey)\"