import runpod
import boto3
import base64
import os
import tempfile

def download_from_s3(s3_config: dict, object_key: str) -> str:
    client = boto3.client(
        "s3",
        aws_access_key_id=s3_config.get("accessId"),
        aws_secret_access_key=s3_config.get("accessSecret"),
        endpoint_url=s3_config.get("endpointUrl"),
    )
    fd, temp_path = tempfile.mkstemp(prefix="filety", suffix="_audio")
    os.close(fd)

    bucket_name = s3_config.get("bucketName")
    client.download_file(bucket_name, object_key, temp_path)

    return temp_path
    

def handler(job):

    _input = job.get("input") or {}
    s3_config = job.get("s3Config") or {}
    task_id = _input.get("task_id")
    model_name = _input.get("model_name", "small")
    language = _input.get("language")
    filename = _input.get("filename") or "audio.wav"
    object_key = _input.get("s3_object_key")

    if not s3_config or not object_key:
        return {
            "status": "error",
            "task_id": task_id,
            "error": "Missing s3Config or s3_object_key",
        }
    
    try:
        temp_path = download_from_s3(s3_config, filename)

        size_bytes = os.path.getsize(temp_path)
        os.remove(temp_path)

        return {
            "status": "success",
            "task_id": task_id,
            "model_name": model_name,
            "language": language,
            "s3_object_key": object_key,
            "file_size_bytes": size_bytes,
            "message": "Audio downloaded from S3 successfully (no transcription yet).",
        }

    except Exception as exc:
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(exc),
        }

runpod.serverless.start({"handler" : handler})
