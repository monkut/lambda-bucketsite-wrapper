# lambda bucketsite wrapper

Yes, s3 buckets provide _STATIC SITE_ operations easily enough.... if you want a public site.
If you want to _protect_ a static site and provide login to a limited number of people things get a bit more difficult.1

This project allows you to serve your _STATIC SITE_ from a bucket through an API Gateway.
The integration of the APIGateway allows you to then integrate CUSTOM auth methods as desired.1

> Admittedly CUSTOM auth is not necessarily easy to integrate, but it's a start.

## Configurable Environment Variables

- BASIC_AUTH_USERNAME 
- BASIC_AUTH_PASSWORD
- BUCKET_NAME
- BUCKET_SITE_PREFIX


## Deploy your site

1. Clone repository:

    ```bash
    git clone https://github.com/monkut/lambda-bucketsite-wrapper.git mysite
    ```

2. create your zappa config:

    > Create your target site bucket prior to creating config.
    > `aws s3api create-bucket --bucket ${BUCKET_NAME} --create-bucket-configuration LocationConstraint=${AWS_DEFAULT_REGION}`

    ```json
    {
        "dev": {
            "app_function": "bucketsite.app.app",
            "aws_region": "ap-northeast-1",
            "profile_name": "YOUR_PROFILE",
            "project_name": "mysite",
            "runtime": "python3.7",
            "keep_warm": false,
            "s3_bucket": "zappa-YOUR_FUNCTION_BUCKET",
            "environment_variables": {
                "BASIC_AUTH_USERNAME": "YOUR_USERNAME",
                "BASIC_AUTH_PASSWORD": "YOUR_PASSWORD",
                "BUCKET_NAME": "YOUR_SITE_BUCKET",
                "BUCKET_SITE_PREFIX": "YOUR_SITE_BUCKET_PREFIX"
            }
        }
    }
    ```
    
2. install and deploy:

    > NOTE:
    > You need the appropriate AWS permissions

    ```
    pipenv install
    pipenv run zappa deploy
    ```

3. Prepare BASIC_AUTH tools:

    ```bash
    cd ~
    git clone https://github.com/monkut/lambda-basicauth-authorizer lambda-basicauth
    cd lambda-basicauth
    pipenv install
    ```

4. Deploy and install custom authorizer:

    ```bash
    pipenv shell
    export BASIC_AUTH_USERNAME={YOUR USERNAME}
    export BASIC_AUTH_PASSWORD={YOUR PASSWORD}
    export PROJECTID={YOUR PROJECT IDENTIFIER}
    export PROJECT_NAME={YOUR PROJECT NAME}  # same as defined in zappa_settings.json
    export RESTAPI_ID=$(aws apigateway get-rest-apis --query "items[?starts_with(name, '${PROJECT_NAME}')].id" --output text)
    make createfuncbucket
    make deploy
    make install
    ```

5. deploy site to bucket:

    ```
    export AWS_PROFILE={MY PROFILE}
    aws s3 sync ${HTML_SOURCE} s3://${YOUR_SITE_BUCKET}/${YOUR_SITE_BUCKET_PREFIX}
    ```