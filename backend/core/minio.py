"""
MinIO client configuration and utilities for object storage.

This module provides a singleton MinIO client instance and utility functions
for file operations including bucket management and file uploads.
"""
import logging
from datetime import timedelta
from typing import Optional, Union, BinaryIO
from io import BytesIO

from minio import Minio, S3Error
from urllib3 import HTTPResponse

from core.config import settings

logger = logging.getLogger(__name__)

class MinIOClient:

    def __init__(self):
        """Initialize MinIO client with settings from config."""
        self._client: Optional[Minio] = None
        self._initialized = False

    def get_client(self) -> Minio:
        """
        Get or create MinIO client instance.

        Returns:
            Minio: Configured MinIO client instance
        """
        if not self._client:
            self._client = Minio(
                f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            logger.info(
                "MinIO client initialized",
                extra={
                    "host": settings.MINIO_HOST,
                    "port": settings.MINIO_PORT,
                    "secure": settings.MINIO_SECURE
                }
            )
        return self._client

    async def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """
        Ensure a bucket exists, create if it doesn't.

        Args:
            bucket_name: Name of the bucket to check/create

        Returns:
            bool: True if bucket exists or was created successfully

        Raises:
            S3Error: If bucket creation fails
        """

        client = self.get_client()

        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                logger.info(
                    "MinIO bucket created",
                    extra={"bucket_name": bucket_name}
                )
            return True
        except S3Error as e:
            logger.error(
                "Failed to ensure bucket exists",
                extra={
                    "bucket_name": bucket_name,
                    "error": str(e),
                    "error_code": e.code
                },
                exc_info=True
            )
            raise

    async def upload_file(
            self,
            bucket_name: str,
            object_name: str,
            file_data: Union[BinaryIO, bytes],
            file_size: int,
            content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload a file to MinIO.

        Args:
            bucket_name: Target bucket name
            object_name: Name for the stored object
            file_data: File-like object containing the data
            file_size: Size of the file in bytes
            content_type: MIME type of the file

        Returns:
            str: Object name of the uploaded file

        Raises:
            S3Error: If upload fails
        """
        client = self.get_client()

        try:
            await self.ensure_bucket_exists(bucket_name)

            if isinstance(file_data, bytes):
                file_data = BytesIO(file_data)

            client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type
            )

            logger.info(
                "File upload to MinIO",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "file_size": file_size,
                    "content_type": content_type
                }
            )

            return object_name
        except S3Error as e:
            logger.error(
                "Failed to upload file to MinIO",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                    "error_code": e.code
                }
            )
            raise

    async def get_file(self, bucket_name: str, object_name: str) -> HTTPResponse:
        """
        Download a file from MinIO.

        Args:
            bucket_name: Source bucket name
            object_name: Name of the object to download

        Returns:
            HTTPResponse: Response containing file data

        Raises:
            S3Error: If download fails
        """
        client = self.get_client()

        try:
            response = client.get_object(bucket_name, object_name)
            logger.info(
                "File downloaded from MinIO",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name
                }
            )
            return response
        except S3Error as e:
            logger.error(
                "Failed to download file from Minio",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                    "error_code": e.code
                },
                exc_info=True
            )
            raise

    async def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete a file from MinIO.

        Args:
            bucket_name: Source bucket name
            object_name: Name of the object to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            S3Error: If deletion fails
        """

        client = self.get_client()

        try:
            client.remove_object(bucket_name, object_name)
            logger.info(
                "File deleted from MinIO",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                }
            )
            return True
        except S3Error as e:
            logger.error(
                "Failed to delete file from MinIO",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                    "error_code": e.code
                },
                exc_info=True
            )
            raise

    async def generate_presigned_url(
            self,
            bucket_name: str,
            object_name: str,
            expires: timedelta = timedelta(hours=1)
    )-> str:
        """
        Generate a presigned URL for temporary file access.

        Args:
            bucket_name: Source bucket name
            object_name: Name of the object
            expires: URL expiration time (default: 1 hour)

        Returns:
            str: Presigned URL

        Raises:
            S3Error: If URL generation fails
        """

        client = self.get_client()

        try:
            url = client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
            logger.info(
                "Presigned url generated",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "expires_in_seconds": expires.total_seconds(),
                }
            )
            return url
        except S3Error as e:
            logger.error(
                "Failed to generate presigned url",
                extra={
                    "bucket_name": bucket_name,
                    "object_name": object_name,
                    "error": str(e),
                    "error_code": e.code
                },
                exc_info=True
            )
            raise


minio_client = MinIOClient()

def get_minio_client() -> MinIOClient:
    return minio_client