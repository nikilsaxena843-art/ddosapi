import os
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn

# ==================== CONFIG ====================
API_KEY = "vipxofficial_vip_system"  # Same as controller
# ===============================================

app = FastAPI()

class ExecuteRequest(BaseModel):
    ip: str
    port: str
    time: str
    threads: str

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return x_api_key

@app.get("/health")
async def health():
    binary_exists = os.path.exists("./soul")
    binary_exec = os.access("./soul", os.X_OK) if binary_exists else False
    return {
        "status": "healthy",
        "pid": os.getpid(),
        "binary_exists": binary_exists,
        "binary_executable": binary_exec
    }

@app.post("/execute")
async def execute(request: ExecuteRequest, x_api_key: str = Header(None)):
    # Verify API key
    verify_api_key(x_api_key)
    
    try:
        # Check if binary exists
        if not os.path.exists("./soul"):
            return {
                "status": "error",
                "output": "Binary 'soul' not found!",
                "return_code": -1
            }
        
        # Make binary executable if needed
        if not os.access("./soul", os.X_OK):
            os.chmod("./soul", 0o755)
        
        # Execute binary with your format: ./soul ip port time threads
        cmd = f"./soul {request.ip} {request.port} {request.time} {request.threads}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        except asyncio.TimeoutError:
            process.kill()
            return {
                "status": "timeout",
                "output": "Execution timed out after 300 seconds",
                "return_code": -1
            }
        
        stdout_text = stdout.decode('utf-8', errors='ignore')
        stderr_text = stderr.decode('utf-8', errors='ignore')
        
        # Return response
        if process.returncode == 0:
            return {
                "status": "completed",
                "output": stdout_text,
                "return_code": 0
            }
        else:
            return {
                "status": "failed",
                "output": f"STDOUT: {stdout_text}\nSTDERR: {stderr_text}",
                "return_code": process.returncode
            }
    
    except Exception as e:
        return {
            "status": "error",
            "output": str(e),
            "return_code": -1
        }

@app.get("/")
async def root():
    return {"status": "worker", "binary": "soul"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)