from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class Waypoint(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None

class TaskAssignment(BaseModel):
    agent: str
    goal: str
    waypoints: List[Waypoint] = []
    constraints: List[str] = []

class SupervisorOutput(BaseModel):
    mission_id: str
    tasks: List[TaskAssignment]
    success_criteria: List[str]

class ScoutStep(BaseModel):
    tool: str
    args: Dict[str, Any] = {}

class ScoutPlan(BaseModel):
    steps: List[ScoutStep]
    notes: Optional[str] = ""
