import runpod
import boto3
import os
import tempfile
from faster_whisper import WhisperModel
import torch

S3_ACCESS_ID = os.getenv("S3_ACCESS_ID")
S3_ACCESS_SECRET = os.getenv("S3_ACCESS_SECRET")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODELS: dict[str, WhisperModel] = {}

def download_from_s3(object_key:str) -> str:
    fd, temp_path = tempfile.mkstemp(prefix="filety_", suffix=".wav")
    os.close(fd)
    

    s3 = boto3.client(
        "s3",
        aws_access_key_id=S3_ACCESS_ID, 
        aws_secret_access_key=S3_ACCESS_SECRET,
        endpoint_url=S3_ENDPOINT_URL,
    )

    s3.download_file(S3_BUCKET_NAME, object_key, temp_path)
    return temp_path

def get_model(model_name: str) -> WhisperModel:
    if model_name not in MODELS:
        MODELS[model_name] = WhisperModel(
            model_name, 
            device=DEVICE,
            compute_type="float16" if DEVICE == "cuda" else "float32"
        )
    return MODELS[model_name]

def handler(job):
    _input = job.get("input", {})
    task_id = _input.get("task_id")
    model_name = _input.get("model", "small")
    object_key = _input.get("s3_object_key")

    ALLOWED = {"small", "medium", "large-v2", "large-v3"}
    if model_name not in ALLOWED:
        return {"status": "error", "task_id": task_id, "error": f"invalid model: {model_name}"}

    if not object_key:
        return {"status": "error", "task_id": task_id, "error": "missing s3_object_key"}
    if not task_id:
        return {"status": "error", "error": "missing task_id"}

    temp_path = None

    try:
        temp_path = download_from_s3(object_key)
        model = get_model(model_name)

        segments, info = model.transcribe(
            temp_path, 
            beam_size=5, 
            vad_filter=True,
        )

        text = " ".join([segment.text for segment in segments])  

        return {
            "status": "success",
            "task_id": task_id,
            "text": text,
        }
    except Exception as e:
        return {
            "status": "error", 
            "task_id": task_id, 
            "error": str(e)
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
runpod.serverless.start({"handler": handler})