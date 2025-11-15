"""Base agent class with common functionality."""

from typing import Optional, Any, Sequence
from abc import ABC, abstractmethod

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import BaseTool

from trialsense.config import get_settings
from trialsense.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all TrialSense agents.

    Provides common functionality:
    - LLM initialization
    - Tool management
    - Prompt templates
    - Execution logic
    """

    def __init__(
        self,
        tools: Optional[list[BaseTool]] = None,
        llm: Optional[BaseChatModel] = None,
        system_prompt: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        Initialize the base agent.

        Args:
            tools: List of LangChain tools available to the agent
            llm: Language model instance (defaults to settings)
            system_prompt: System prompt for the agent
            verbose: Enable verbose logging
        """
        self.settings = get_settings()
        self.tools = tools or []
        self.llm = llm or self._create_llm()
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.verbose = verbose

        # Create agent executor
        self.agent_executor = self._create_agent_executor()

    def _create_llm(self) -> BaseChatModel:
        """Create LLM instance based on configuration."""
        settings = self.settings

        if settings.default_llm.startswith("gpt"):
            if not settings.has_openai_key():
                raise ValueError("OpenAI API key not configured")

            return ChatOpenAI(
                model=settings.default_llm,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.openai_api_key,
            )
        elif settings.default_llm.startswith("claude"):
            if not settings.has_anthropic_key():
                raise ValueError("Anthropic API key not configured")

            return ChatAnthropic(
                model=settings.default_llm,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                api_key=settings.anthropic_api_key,
            )
        else:
            raise ValueError(f"Unsupported model: {settings.default_llm}")

    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for this agent."""
        pass

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the prompt template for the agent."""
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def _create_agent_executor(self) -> AgentExecutor:
        """Create the agent executor."""
        prompt = self._create_prompt_template()

        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.settings.agent_max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    async def arun(
        self,
        input_text: str,
        chat_history: Optional[Sequence] = None,
    ) -> dict[str, Any]:
        """
        Run the agent asynchronously.

        Args:
            input_text: User input
            chat_history: Previous conversation messages

        Returns:
            Agent response with output and intermediate steps
        """
        logger.info(f"Running {self.__class__.__name__}")

        result = await self.agent_executor.ainvoke({
            "input": input_text,
            "chat_history": chat_history or [],
        })

        return result

    def run(
        self,
        input_text: str,
        chat_history: Optional[Sequence] = None,
    ) -> dict[str, Any]:
        """
        Run the agent synchronously.

        Args:
            input_text: User input
            chat_history: Previous conversation messages

        Returns:
            Agent response with output and intermediate steps
        """
        import asyncio
        return asyncio.run(self.arun(input_text, chat_history))
