from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SupervisorInput(BaseModel):
    sample_data: List[Dict[str, Any]]
    description: List[Dict[str, Any]]
    offline_mode: bool = False


class SupervisorOutput(BaseModel):
    libraries: List[str]
    tasks: List[Dict[str, Any]]


class MetadataInput(BaseModel):
    sample_data: List[Dict[str, Any]]
    schema_info: Dict[str, Any]
    description: Dict[str, Any]
    offline_mode: bool = False


class AssistantInput(BaseModel):
    supervisor_response: Dict[str, Any]
    path: str
    offline_mode: bool = False


class AssistantOutput(BaseModel):
    name: str = ""
    code: str = ""


# Keep it simple for generic runner for now
class AgentRunRequest(BaseModel):
    agent_type: str
    payload: Dict[str, Any]


class InsightsInput(BaseModel):
    img: str
    summary_data: Dict[str, Any]
    sample_data: List[Dict[str, Any]]
    description: Dict[str, Any]
    offline_mode: bool = False


class SandboxInput(BaseModel):
    code: str
    data_dir: str = "data"
    image: str = "llm-sandbox"
    name: Optional[str] = None
    sample_data: List[Dict[str, Any]] = []
    filename: str = "data.csv"
