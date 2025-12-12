import runpod
import boto3
import os
import tempfile
import wisper
import torch

S3_ACCESS_ID = os.getenv("S3_ACCESS_ID")
S3_ACCESS_SECRET = os.getenv("S3_ACCESS_SECRET")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

if not all([S3_ACCESS_ID, S3_ACCESS_SECRET, S3_BUCKET_NAME, S3_ENDPOINT_URL]):
    raise RuntimeError("Missing S3 env vars: S3_ACCESS_ID/S3_ACCESS_SECRET/S3_BUCKET_NAME/S3_ENDPOINT_URL")

s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_ID,
    aws_secret_access_key=S3_ACCESS_SECRET,
    endpoint_url=S3_ENDPOINT_URL,
    region_name="eu-ro-1"

)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "openai/whisper-large-v2"

model = wisper.load_model(MODEL_NAME, device=DEVICE)

def download_from_s3(s3_config: dict, object_key: str) -> str:
    fd, temp_path = tempfile.mkstemp(prefix="filety", suffix="_audio")
    os.close(fd)

    s3.download_file(S3_BUCKET_NAME, object_key, temp_path)
    return temp_path


def handler(job):

    _input = job.get("input") or {}
    task_id = _input.get("task_id")
    object_key = _input.get("s3_object_key")

    if not object_key:
        return {"status": "error", "task_id": task_id, "error": "Missing s3_object_key"}

    try:
        temp_path = download_from_s3(object_key)
        size_bytes = os.path.getsize(temp_path)
        
        result = model.transcribe(temp_path)

        text = result.get("text", "").strip()

        return {
            "status": "success",
            "task_id": task_id,
            "s3_object_key": object_key,
            "file_size_bytes": size_bytes,
            "text": text, 
            "message": "Audio downloaded from S3 successfully.",
        }
    except Exception as exc:
        return {"status": "error", "task_id": task_id, "error": str(exc)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

runpod.serverless.start({"handler" : handler})
