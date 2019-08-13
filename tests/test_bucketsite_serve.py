import base64
import logging
import sys
from pathlib import Path
from unittest import TestCase

import boto3
from bucketsite.app import app
from bucketsite.settings import (
    BASIC_AUTH_PASSWORD,
    BASIC_AUTH_USERNAME,
    BOTO3_ENDPOINTS,
    BUCKET_NAME,
    BUCKET_SITE_PREFIX,
)

TESTDATA_DIRECTORY = Path(__file__).parent / "testdata"

S3 = boto3.client("s3", endpoint_url=BOTO3_ENDPOINTS["s3"])

# reduce logging output from noisy packages
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)

token = base64.b64encode(
    f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode("utf8")
).decode("utf8")
BASIC_AUTH_HEADER = {"Authorization": f"Basic {token}"}

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(funcName)s: %(message)s",
)


class BucketSiteServe(TestCase):
    def setUp(self):

        # delete bucket
        try:
            response = S3.list_objects(Bucket=BUCKET_NAME)
            keys = [{"Key": s3file["Key"]} for s3file in response["Contents"]]
            if keys:
                S3.delete_objects(Bucket=BUCKET_NAME, Delete={"Objects": keys})
        except:
            pass
        try:
            S3.delete_bucket(Bucket=BUCKET_NAME)
        except:
            pass

        # create bucket
        S3.create_bucket(Bucket=BUCKET_NAME)

        # populate bucket with site
        for item in TESTDATA_DIRECTORY.rglob("*"):
            if item.is_file():
                with item.open("rb") as upload_file:
                    relitem = item.relative_to(TESTDATA_DIRECTORY)
                    relative_filepath = "/".join(relitem.parts)
                    S3.put_object(
                        Body=upload_file,
                        Bucket=BUCKET_NAME,
                        Key=f"{BUCKET_SITE_PREFIX}{relative_filepath}",
                    )

        # add other files to other sit prefix
        for item in TESTDATA_DIRECTORY.rglob("*"):
            if item.is_file():
                with item.open("rb") as upload_file:
                    relitem = item.relative_to(TESTDATA_DIRECTORY)
                    relative_filepath = "/".join(relitem.parts)
                    S3.put_object(
                        Body=upload_file,
                        Bucket=BUCKET_NAME,
                        Key=f"othersiteprefix/{relative_filepath}",
                    )
        response = S3.list_objects(Bucket=BUCKET_NAME)
        self.client = app.test_client()

    def test_app_auth(self):
        index_url = "/index.html"
        response = self.client.get(index_url)
        expected = 401
        actual = response.status_code
        msg = f"actual({actual}) != expected({expected}): {response.data}"
        self.assertTrue(actual == expected, msg)

    def test_app_serve_notexists(self):
        index_url = "/nofile.html"
        response = self.client.open(index_url, method="GET", headers=BASIC_AUTH_HEADER)
        expected = 404
        actual = response.status_code
        msg = f"actual({actual}) != expected({expected}): {response.data}"
        self.assertTrue(actual == expected, msg)

    def test_app_serve_exists(self):
        index_url = "/index.html"
        response = self.client.open(index_url, method="GET", headers=BASIC_AUTH_HEADER)
        expected = 200
        actual = response.status_code
        msg = f"actual({actual}) != expected({expected}): {response.data}"
        self.assertTrue(actual == expected, msg)

        css_url = "/css/main.css"
        response = self.client.open(css_url, method="GET", headers=BASIC_AUTH_HEADER)
        expected = 200
        actual = response.status_code
        msg = f"actual({actual}) != expected({expected}): {response.data}"
        self.assertTrue(actual == expected, msg)

    def test_app_serve_relativeattempt(self):
        url = "/../index.html"
        response = self.client.open(url, method="GET", headers=BASIC_AUTH_HEADER)
        expected = 404
        actual = response.status_code
        msg = f"actual({actual}) != expected({expected}): {response.data}"
        self.assertTrue(actual == expected, msg)
