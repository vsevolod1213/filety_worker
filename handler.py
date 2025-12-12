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

s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_ID,
    aws_secret_access_key=S3_ACCESS_SECRET,
    endpoint_url=S3_ENDPOINT_URL,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = wisper.load_model("openai/whisper-large-v2", device=DEVICE)

def download_from_s3(s3_config, object_key):
    fd, temp_path = tempfile.mkstemp(prefix="filety_", suffix=".audio")
    os.close(fd)

    s3client = boto3.client(
        "s3",
        aws_access_key_id=s3_config["accessId"],
        aws_secret_access_key=s3_config["accessSecret"],
        endpoint_url=s3_config["endpointUrl"],
    )

    s3client.download_file(s3_config["bucketName"], object_key, temp_path)
    return temp_path

def handler(job):
    _input = job["input"]
    s3_config = job["s3Config"]

    object_key = _input.get("s3_object_key")
    task_id = _input.get("task_id")

    if not object_key:
        return {"status": "error", "error": "missing object_key"}

    temp_path = None

    try:
        temp_path = download_from_s3(s3_config, object_key)

        result = MODEL.transcribe(temp_path)
        text = result["text"].strip()

        return {
            "status": "success",
            "task_id": task_id,
            "text": text,
        }
    except Exception as e:
        return {"status": "error", "task_id": task_id, "error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
