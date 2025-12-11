import runpod

import base64
import os
import tempfile

def save_base64_to_file(audio_base64: str, file_name: str | None = None) -> str:
    if not file_name:
        file_name = "audio.wav"

    fd, temp_path = tempfile.mkstemp(prefix="filety_", suffix="_" + file_name)
    os.close(fd)

    binary = base64.b64decode(audio_base64)
    with open(temp_path, "wb") as f:
        f.write(binary)

    return temp_path

def handler(job):

    _input = job.get("input") or {}

    task_id = _input.get("task_id")
    model_name = _input.get("model_name", "small")
    language = _input.get("language")
    filename = _input.get("filename") or "audio.wav"
    audio_b64 = _input.get("audio_base64")

    if not audio_b64:
        return {
            "status": "error",
            "task_id": task_id,
            "error": "audio_base64 is required",
        }
    
    try:
        temp_path = save_base64_to_file(audio_b64, filename)

        size_bytes = os.path.getsize(temp_path)
        os.remove(temp_path)

        return {
            "status": "success",
            "task_id": task_id,
            "model_name": model_name,
            "language": language,
            "filename": filename,
            "file_size_bytes": size_bytes,
            "message": "Audio received and decoded successfully (no transcription yet)."
        }

    except Exception as exc:
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(exc),
        }

runpod.serverless.start({"handler" : handler})
