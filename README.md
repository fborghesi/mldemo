# mldemo-api
Demo application with different models for testing and learning purposes.

## Deploy the Backend 

This project provides a Makefile in the root folder that will let you build
and deploy the backend to AWS as a set of lambda functions and related resources
necessary for it to work.

First you'll need to define your settings. There's an example file named 
**dot.env-ENV**, just copy it to *.env-<env_name>* (i.e. *.env-dev*, 
*.env-prod*, etc.) and update your environment settings there.

### Building and Deploying the base images
This project is based on two docker images, one for python dependencies and the 
other for ML dependencies. These images are quite large and take a long time to
build/upload and since they're not expected to change frequently they can be 
built separately from the rest.

You just do that by running:
```shell
make images
```
This will build both images and deploy them to the AWS ECR. You can build them 
individually if you want by running:
```shell
make python-base
make model-base
```

### Building and Deploying the lambda functions
AWS Lambda functions are also docker images. There's a command that will take 
care of building the images, packaging them, uploading them to the ECR and 
deploying all the resources on the cloud. 

The command is:
```shell
make deploy
```

## Front-end Set Up
First of all you'll need to get the redirect URL which must be set in different
places for components to be in sync for OAUTH to work properly.

You should take note on the **API ID** you'll be working with and the **AWS 
Zone** the login API is being deployed to. You can get the **API ID** from your 
[API Gateway Console](https://console.aws.amazon.com/apigateway/main), just 
select the right AWS Zone where your user login lambda functions have been 
deployed to (say *us-east-1*). That will get you a table with all available
Gateways, with their respective ID's in one of the columns.

With that you will be able to build the public backend url which is composed 
like:

```
https://<GATEWAY_ID>.execute-api.<AWS_ZONE>.amazonaws.com/dev
```

As an example, the current looks like:
```properties
https://vnz3cekgog.execute-api.us-east-1.amazonaws.com/dev
```

### Environment
Environment variable NEXT_PUBLIC_BACKEND_URL must point to the base AWS endpoint
where user login functions live. If you're running the project locally, you can
just edit the *.env* file in your front-end's project root and set the following
entry:

```
NEXT_PUBLIC_BACKEND_URL=https://vnz3cekgog.execute-api.us-east-1.amazonaws.com/dev
```

If you're running the front-end from Vercel, you just need to log in and then:
 * Click on the project you're trying to set up.
 * Click on *Settings*.
 * Click on *Environment Variables*.
 * Scroll down and make sure **NEXT_PUBLIC_BACKEND_URL** exists. If it does, just 
update its value. Otherwise create the new entry.


### Google Cloud Auth
If you're using Google for Authentication, you'll need to:
 * Go to your [APIs and Services](https://console.cloud.google.com/apis/) 
section in the Console.
 * Click on *Credentials* in the menu on the left.
 * Click on the right OAUTH2 Client from the *OAuth 2.0 Client IDs* table. 
 * In the *Authorized redirect URIs* section, make sure there's an entry 
containing the redirect URL for your front-end.