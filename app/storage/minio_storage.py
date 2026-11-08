from collections.abc import Iterator
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageError(RuntimeError):
    """Raised when an object cannot be stored or retrieved."""


def get_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio | None = None) -> Minio:
    client = client or get_client()
    try:
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
    except S3Error as exc:
        raise StorageError("No se pudo preparar el bucket de audio") from exc
    return client


def put_file(path: Path, object_name: str, content_type: str) -> None:
    client = ensure_bucket()
    try:
        with path.open("rb") as file_data:
            client.put_object(
                settings.minio_bucket,
                object_name,
                file_data,
                length=path.stat().st_size,
                content_type=content_type,
            )
    except (OSError, S3Error) as exc:
        raise StorageError("No se pudo almacenar el archivo de audio") from exc


def remove_file(object_name: str) -> None:
    try:
        get_client().remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        raise StorageError("No se pudo eliminar el archivo de audio") from exc


def download_file(object_name: str, destination: Path) -> None:
    response = None
    try:
        response = get_client().get_object(settings.minio_bucket, object_name)
        with destination.open("wb") as file_data:
            for chunk in response.stream(64 * 1024):
                file_data.write(chunk)
    except (OSError, S3Error) as exc:
        raise StorageError("No se pudo descargar el archivo de audio") from exc
    finally:
        if response is not None:
            response.close()
            response.release_conn()


def stream_file(object_name: str) -> Iterator[bytes]:
    response = None
    try:
        response = get_client().get_object(settings.minio_bucket, object_name)
        for chunk in response.stream(64 * 1024):
            yield chunk
    except S3Error as exc:
        raise StorageError("No se pudo leer el archivo de audio") from exc
    finally:
        if response is not None:
            response.close()
            response.release_conn()
