from fastapi import APIRouter, HTTPException
import logging
import traceback
from agents.agent_factory import AgentFactory, AgentType
from schemas.agent_io import (
    SupervisorInput,
    AssistantInput,
    AgentRunRequest,
    AgentRunRequest,
    InsightsInput,
    SandboxInput,
    MetadataInput,
)
from sandbox.sandbox import run_in_docker_sandbox
from sandbox.sandbox import run_in_docker_sandbox

logger = logging.getLogger(__name__)
router = APIRouter()

# Global agent cache to avoid reloading models
_agent_cache = {}

def get_agent_cached(agent_type: AgentType):
    """Get or create cached agent instance."""
    if agent_type not in _agent_cache:
        _agent_cache[agent_type] = AgentFactory.get_agent(agent_type)
    return _agent_cache[agent_type]


@router.get("/health")
async def health_check():
    return {"status": "ok", "cached_agents": list(_agent_cache.keys())}


@router.post("/agents/metadata/run")
async def run_metadata(input_data: MetadataInput):
    try:
        agent = get_agent_cached(AgentType.METADATA)
        result = agent.run(
            sample_data=input_data.sample_data,
            schema=input_data.schema_info,
            description=input_data.description,
            offline_mode=input_data.offline_mode,
        )
        return result
    except Exception as e:
        logger.error(f"Error in metadata agent: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/supervisor/run")
async def run_supervisor(input_data: SupervisorInput):
    try:
        agent = get_agent_cached(AgentType.SUPERVISOR)
        result = agent.run(
            sample_data=input_data.sample_data,
            description=input_data.description,
            offline_mode=input_data.offline_mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/assistant/run")
async def run_assistant(input_data: AssistantInput):
    try:

        agent = get_agent_cached(AgentType.ASSISTANT)
        result = agent.run(
            supervisor_response=input_data.supervisor_response,
            path=input_data.path,
            offline_mode=input_data.offline_mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/generic/run")
async def run_generic_agent(request: AgentRunRequest):
    try:
        # Convert string to enum
        try:
            agent_type_enum = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type: {request.agent_type}"
            )

        agent = get_agent_cached(agent_type_enum)

        # We need to unpack the payload as arguments to run.
        # This is a bit unsafe without validation but fits the generic requirement.
        result = agent.run(**request.payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/insights/run")
async def run_insights(input_data: InsightsInput):
    try:
        agent = get_agent_cached(AgentType.INSIGHTS)
        result = agent.run(
            img=input_data.img,
            summary_data=input_data.summary_data,
            sample_data=input_data.sample_data,
            description=input_data.description,
            offline_mode=input_data.offline_mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sandbox/run")
async def run_sandbox(input_data: SandboxInput):
    try:
        # Note: In a real production environment, strict security measures
        # are needed for arbitrary code execution.
        result = run_in_docker_sandbox(
            code=input_data.code,
            data_dir=input_data.data_dir,
            image=input_data.image,
            name=input_data.name,
            sample_data=input_data.sample_data,
            filename=input_data.filename,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
