import os
import boto3
from pathlib import Path


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

    public_url = os.getenv("R2_PUBLIC_URL")
    return f"{public_url}/{object_key}"