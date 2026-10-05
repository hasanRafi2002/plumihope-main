import uuid

import boto3

from app.core.config import settings

_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
)


def build_object_key(owner_id: uuid.UUID, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    return f"uploads/{owner_id}/{uuid.uuid4()}.{ext}"


def upload_file(object_key: str, file_bytes: bytes, content_type: str) -> None:
    _s3_client.put_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )


def generate_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    return _s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )


def download_file(object_key: str) -> bytes:
    response = _s3_client.get_object(Bucket=settings.s3_bucket, Key=object_key)
    return response["Body"].read()
