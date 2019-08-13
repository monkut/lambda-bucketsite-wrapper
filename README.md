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

0. Copy your _STATIC SITE_ to the desired bucket

1. create your zappa config:

    ```json
    {
        "dev": {
            "app_function": "app.app",
            "aws_region": "ap-northeast-1",
            "profile_name": "YOUR_PROFILE",
            "project_name": "mysite",
            "runtime": "python3.7",
            "s3_bucket": "zappa-YOUR_FUNCTION_BUCKET",
            "environment_variables": {
                "BASIC_AUTH_USERNAME": "YOUR_USERNAME",
                "BASIC_AUTH_PASSWORD": "YOUR_PASSWORD",
                "BUCKET_NAME": "YOUR_BUCKET",
                "BUCKET_SITE_PREFIX": "YOUR PREFIX"
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


## Integrate BASIC AUTH