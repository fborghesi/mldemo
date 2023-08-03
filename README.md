# mldemo-api
Demo application with different models for testing and learning purposes.

## Deploy the application

You'll need to build the project first, be sure to replace 
**$API_DIR** and **$ECR_REPO** so that they will be properly replaced in the 
commands below: 

```bash
# path to the API directory where the project lives
export API_DIR=.

# the elastic container repo where your images will be stored
export ECR_REPO=491431825058.dkr.ecr.us-east-1.amazonaws.com/mldemo
```

``bash
% sam build \
    --template $API_DIR/template.yaml \
    --build-dir $API_DIR/.aws-sam/build \
    --use-container
``

Now it's time to package the project and upload the images, for that to happen
you'll need a bucket (in my case it's *mldemo-data-upload-bucket*) where to
upload the files and an ECR repo to store your images.

``bash
% sam package \
    --template-file $API_DIR/.aws-sam/build/template.yaml \
    --output-template-file $API_DIR/.aws-sam/build/packaged-template.yaml \
    --s3-bucket mldemo-data-upload-bucket \
    --image-repository $ECR_REPO
``

The final step is the actual deployment:

```bash
sam deploy deploy \
  --template-file $API_DIR/.aws-sam/build/template.yaml \
  --stack-name mldemo-stack-prod \
  --s3-bucket mldemo-data-upload-bucket \
  --image-repository $ECR_REPO \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-execute-changeset \
  --parameter-overrides \
  \"LambdaEnvironment\"=\"<environment-name>\" \
  \"DatabaseHost\"=\"mldemocluster.wvbvp.mongodb.net\" \
  \"DatabasePort\"=\"27017\" \
  \"DatabaseUser\"=\"<mongodb-database-user>\" \
  \"DatabasePassword\"=\"<mongodb-database-password>\" \
  \"DatabaseName\"=\"<mongodb-database-name>\" \
  \"CorsAllowedHeaders\"=\"*\" \
  \"CorsAllowedOrigin\"=\"*\" \
  \"CorsAllowedMethods\"=\"*\" \
  \"SessionTimeoutMins\"=\"720\" \
  \"GoogleAuthClientSecret\"=\"<google-auto-client-secret>\" \
  \"GoogleAuthRedirectDevUrl\"=\"http://localhost:3000/authorize\" \
  \"GoogleAuthRedirectProdUrl\"=\"https://<prod_domain>/authorize\" 
```

