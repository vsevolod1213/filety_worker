import runpod

def handler(job):

    job_input = job.get("input", {})

    return{
        "status": "success",
        "data": job_input
    }

runpod.serverless.start({"handler" : handler})