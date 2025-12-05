import uvicorn
from app.insecure.main import app
import os
import sys


sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

if __name__ == "__main__":
    
    uvicorn.run(app, host="127.0.0.1", port=8002)