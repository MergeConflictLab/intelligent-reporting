from enum import Enum

from .base_agent import Agent



class AgentType(Enum):
    METADATA = "metadata"
    SUPERVISOR = "supervisor"
    ASSISTANT = "assistant"
    INSIGHTS = "insights"
    # STORYTELLER = "storyteller"


class AgentFactory:
    """
    Factory for creating agent instances.
    """

    @staticmethod
    def get_agent(agent_type: AgentType) -> Agent:
        if agent_type == AgentType.METADATA:
            from .metadata_agent import MetadataAgent

            return MetadataAgent()
        elif agent_type == AgentType.SUPERVISOR:
            from .supervisor_agent import SupervisorAgent

            return SupervisorAgent()
        elif agent_type == AgentType.ASSISTANT:
            from .assistant_agent import AssistantAgent

            return AssistantAgent()
        elif agent_type == AgentType.INSIGHTS:
            from .insights_agent import InsightsAgent

            return InsightsAgent()
        # elif agent_type == AgentType.STORYTELLER:
        #     from intelligent_reporting.agents.storyteller_agent import StorytellerAgent
        #
        #     return StorytellerAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
