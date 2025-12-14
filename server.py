from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add current directory to path so we can import Friday1.0
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the agent
# Note: We assume Friday1.0.py is in the same directory and has the class GoogleWorkspaceAgent
# We rename the file import to avoid syntax errors if it has dots, but standard import works if name is valid
# Since the file is named "Friday1.0.py", we might need to use importlib
import importlib.util
spec = importlib.util.spec_from_file_location("FridayAgent", "Friday1.0.py")
friday_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(friday_module)

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
try:
    agent = friday_module.GoogleWorkspaceAgent()
    print("[SERVER] Agent initialized successfully")
except Exception as e:
    print(f"[SERVER] Error initializing agent: {e}")
    agent = None

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "Friday API is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        response = agent.process_request(request.message)
        
        # Simple parsing to detect "Rich Cards" based on response text
        # This is a basic implementation. Ideally, the agent should return structured data.
        card_type = None
        card_data = {}
        
        if "[EVENT]" in response or "created successfully" in response and "Event" in response:
            card_type = "calendar_event"
        elif "[FILE]" in response or "File" in response and "created" in response:
            card_type = "drive_file"
        elif "[EMAIL]" in response:
            card_type = "email_list"
            
        return {
            "response": response,
            "card_type": card_type,
            "card_data": card_data # Placeholder for now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
def get_dashboard_data():
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        files = agent.drive_agent.get_files_data()
        events = agent.calendar_agent.get_events_data()
        
        return {
            "recent_files": files,
            "upcoming_events": events
        }
    except Exception as e:
        print(f"[SERVER] Error fetching dashboard data: {e}")
        return {"recent_files": [], "upcoming_events": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
