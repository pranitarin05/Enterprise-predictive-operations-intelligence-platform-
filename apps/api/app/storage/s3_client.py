"""
MinIO/S3-compatible client setup.

Because MinIO speaks the exact S3 API, this same client and code will
work unchanged against real AWS S3 in production — only settings.s3_endpoint_url
changes (or is simply omitted for real AWS).
"""

import boto3
from botocore.exceptions import ClientError

from app.config.settings import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)


def check_storage_connection() -> bool:
    """Used by the health check — confirms we can list buckets."""
    try:
        s3_client.list_buckets()
        return True
    except ClientError:
        return False
