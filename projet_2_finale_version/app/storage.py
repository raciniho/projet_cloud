import os
from minio import Minio
from minio.error import S3Error
import io

class MinioHandler:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False
        )
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "files")
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_file(self, object_name: str, data: io.BytesIO, length: int, content_type: str):
        self.client.put_object(
            self.bucket_name,
            object_name,
            data,
            length,
            content_type=content_type
        )

    def get_file(self, object_name: str):
        try:
            return self.client.get_object(self.bucket_name, object_name)
        except S3Error as e:
            print(f"Error getting file: {e}")
            return None

    def delete_file(self, object_name: str):
        self.client.remove_object(self.bucket_name, object_name)

    def get_file_url(self, object_name: str):
        # Presigned URL for temporary access if needed, or just handle streaming in API
        return self.client.presigned_get_object(self.bucket_name, object_name)

minio_handler = MinioHandler()
