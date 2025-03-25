import logging
import os
import sys
from http import HTTPStatus
from mimetypes import MimeTypes

import boto3
from flask import Flask, Response, abort, request, send_file, redirect
from flask_basicauth import BasicAuth

from .settings import (
    BASIC_AUTH_PASSWORD,
    BASIC_AUTH_USERNAME,
    BOTO3_ENDPOINTS,
    BUCKET_NAME,
    BUCKET_SITE_PREFIX,
)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(funcName)s: %(message)s",
)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

app = Flask(__name__)  # pylint: disable=invalid-name

app.config["BASIC_AUTH_USERNAME"] = BASIC_AUTH_USERNAME
app.config["BASIC_AUTH_PASSWORD"] = BASIC_AUTH_PASSWORD
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
logger.warning(app.config["BASIC_AUTH_USERNAME"])
logger.warning(app.config["BASIC_AUTH_PASSWORD"])
app.config["BASIC_AUTH_FORCE"] = True
if not app.config["BASIC_AUTH_PASSWORD"] or not app.config["BASIC_AUTH_USERNAME"]:
    raise ValueError(
        f"Required environment variable not set: BASIC_AUTH_PASSWORD or BASIC_AUTH_USERNAME"
    )
basic_auth = BasicAuth(app)  # pylint: disable=invalid-name

S3 = boto3.client("s3", endpoint_url=BOTO3_ENDPOINTS["s3"])
MAX_LAMBDA_RESPONSE_BYTES = 6291456


@app.route("/<path:path>")
@basic_auth.required
def serve(path: str) -> Response:
    """Serve collection html in defined SITE_DIRECTORY_RELPATH"""
    logger.debug(f"headers: {request.headers}")
    if os.path.isabs(path) or ".." in path:
        abort(HTTPStatus.NOT_FOUND)
    prefix = BUCKET_SITE_PREFIX
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    key = f"{prefix}{path}"
    try:
        response = S3.get_object(Bucket=BUCKET_NAME, Key=key)
    except S3.exceptions.NoSuchKey:
        logger.warning(f"Key({key}) not found in: {BUCKET_NAME}")
        abort(HTTPStatus.NOT_FOUND)

    if path and "Body" in response:
        mimer = MimeTypes()
        filename, *_ = path.split("?")
        file_mimetype = mimer.guess_type(filename)[0]

        if not file_mimetype:
            font_mimetypes = {
                ".woff": "font/woff",
                ".woff2": "font/woff2",
                ".ttf": "font/ttf",
                ".webp": "image/webp",
            }
            for font_ext, font_mimetype in font_mimetypes.items():
                if filename.endswith(font_ext):
                    file_mimetype = font_mimetype
                    break
        if not file_mimetype:
            logger.warning(f"Unable to determine mimetype: {filename} {path}")
        request_file = response["Body"]
        content_length_bytes = response["ContentLength"]
        if content_length_bytes > MAX_LAMBDA_RESPONSE_BYTES:
            logger.warning(
                f"File too large to serve, re-directing to s3 content: {filename} {path} {content_length_bytes}"
            )
            presigned_url = S3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
                HttpMethod="GET",
            )
            return redirect(presigned_url)
        else:
            return send_file(request_file, add_etags=False, mimetype=file_mimetype)
    abort(HTTPStatus.NOT_FOUND)
