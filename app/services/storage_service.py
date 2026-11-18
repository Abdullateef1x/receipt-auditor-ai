import os
import boto3
from pathlib import Path
from urllib.parse import urlparse, unquote


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def upload_report_to_r2(report_path: str) -> str:
    client = get_r2_client()
    bucket = os.getenv("R2_BUCKET_NAME")

    file_name = Path(report_path).name
    object_key = f"reports/{file_name}"

    client.upload_file(
        Filename=report_path,
        Bucket=bucket,
        Key=object_key,
        ExtraArgs={"ContentType": "application/pdf"},
    )

    return object_key


def generate_report_download_url(object_key: str) -> str:
    client = get_r2_client()
    bucket = os.getenv("R2_BUCKET_NAME")

    # Support older database records containing full URLs.
    if object_key.startswith(("http://", "https://")):
        object_key = unquote(urlparse(object_key).path.lstrip("/"))

        # Remove the bucket prefix if the URL contains it.
        bucket_prefix = f"{bucket}/"
        if object_key.startswith(bucket_prefix):
            object_key = object_key[len(bucket_prefix):]

    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
        },
        ExpiresIn=3600,
    )
