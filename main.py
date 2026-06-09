from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, get_db, Base
from models import Incident
from agent import analyze_incident
import models

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SAP Incident Intelligence System")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
def ui():
    return FileResponse("static/index.html")

class IncidentRequest(BaseModel):
    error_message: str

class IncidentResponse(BaseModel):
    id: int
    sap_module: str
    root_cause: str
    impact: str
    resolution_steps: str
    severity: str

@app.get("/")
def root():
    return {"message": "SAP Incident Intelligence System is running"}

@app.post("/analyze")
def analyze(request: IncidentRequest, db: Session = Depends(get_db)):
    if not request.error_message.strip():
        raise HTTPException(status_code=400, detail="Error message cannot be empty")
    # Step 1 — Check if we've seen a similar error before
    existing = db.query(Incident).filter(
        Incident.error_message.ilike(f"%{request.error_message[:50]}%")
    ).first()

    if existing:
        return {
            "id": existing.id,
            "sap_module": existing.sap_module,
            "root_cause": existing.root_cause,
            "impact": existing.impact,
            "resolution_steps": existing.resolution_steps,
            "severity": "HIGH",
            "source": "cache"  # Tells you this came from DB, not AI
        }

    try:
        # Run AI analysis
        result = analyze_incident(request.error_message)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
    # Save to database. only reaches here if AI analysis succeeded and returned valid JSON
    incident = Incident(
        error_message=request.error_message,
        sap_module=result.get("sap_module"),
        root_cause=result.get("root_cause"),
        impact=result.get("impact"),
        resolution_steps=result.get("resolution_steps")
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "id": incident.id,
        "sap_module": result.get("sap_module"),
        "root_cause": result.get("root_cause"),
        "impact": result.get("impact"),
        "resolution_steps": result.get("resolution_steps"),
        "severity": result.get("severity"),
        "source": "ai"
    }

@app.get("/incidents")
def get_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    return incidents

@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident