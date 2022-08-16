# insurance-api
Demo application with different models for testing and learning purposes.

## Deploy the application

You'll need to build the project first, be sure to replace 
**<insurance-api-dir>** with the actual directory where your project lives in the 
command below:

``bash
% sam build \
    --template <insurance-api-dir>/template.yaml \
    --build-dir <insurance-api-dir>/.aws-sam/build \
    --use-container
``

Now it's time to package the project and upload the images, for that to happen
you'll need a bucket (in my case it's *insurance-data-upload-bucket*) where to
upload the files and an ECR repo to store your images.


``bash
% sam package \
    --template-file <insurance-api-dir>/.aws-sam/build/template.yaml \
    --output-template-file <insurance-api-dir>/.aws-sam/build/packaged-template.yaml \
    --s3-bucket insurance-data-upload-bucket 
    --image-repository 012345678912.dkr.ecr.us-east-1.amazonaws.com/insurance
``

The final step is the actual deployment:

```bash
sam deploy deploy \
  --template-file <insurance-api-dir>/.aws-sam/build/template.yaml \
  --stack-name insurance-stack-prod \
  --s3-bucket insurance-data-upload-bucket \
  --image-repository 012345678912.dkr.ecr.us-east-1.amazonaws.com/insurance \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-execute-changeset \
  --parameter-overrides \
  \"LambdaEnvironment\"=\"<environment-name>\" \
  \"DatabaseHost\"=\"insurancecluster.wvbvp.mongodb.net\" \
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

