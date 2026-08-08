"""Pre-built LangChain agent adapter with trace capture."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from app.models.trace import Trace, Span, TokenUsage
from app.services.tracing import trace_service


class LangChainAgentAdapter:
    """Adapter for LangChain agents with automatic trace capture."""

    def __init__(self, agent, agent_type: str = "langchain"):
        """Initialize LangChain adapter.

        Args:
            agent: LangChain agent instance
            agent_type: Type identifier for the agent
        """
        self.agent = agent
        self.agent_type = agent_type

    @trace_service.observe_agent(name="langchain_agent")
    async def run(
        self,
        input: str,
        run_id: str,
        agent_id: str,
        **kwargs
    ) -> str:
        """Run LangChain agent with input and capture trace.

        Args:
            input: User input
            run_id: Evaluation run ID
            agent_id: Agent ID
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        # Run the LangChain agent
        response = await self._invoke_agent(input, run_id, **kwargs)

        # Extract output from response
        if hasattr(response, 'output'):
            return response.output
        elif isinstance(response, dict):
            return response.get('output', str(response))
        else:
            return str(response)

    @trace_service.observe_llm(name="langchain_llm_call")
    async def _invoke_agent(
        self,
        input: str,
        run_id: str,
        **kwargs
    ) -> Any:
        """Invoke LangChain agent with trace capture.

        Args:
            input: User input
            run_id: Run ID for tracing
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        # Invoke the agent
        if hasattr(self.agent, 'ainvoke'):
            response = await self.agent.ainvoke({"input": input}, **kwargs)
        elif hasattr(self.agent, 'arun'):
            response = await self.agent.arun(input, **kwargs)
        else:
            # Fallback to sync version
            if hasattr(self.agent, 'invoke'):
                response = self.agent.invoke({"input": input}, **kwargs)
            else:
                response = self.agent.run(input, **kwargs)

        return response


class LangChainAgentAdapterWithTools(LangChainAgentAdapter):
    """LangChain adapter with tool execution tracking."""

    def __init__(self, agent, tools: Optional[List] = None):
        """Initialize with tools.

        Args:
            agent: LangChain agent instance
            tools: List of LangChain tools
        """
        super().__init__(agent)
        self.tools = tools or []

    @trace_service.observe_agent(name="langchain_agent_with_tools")
    async def run(
        self,
        input: str,
        run_id: str,
        agent_id: str,
        **kwargs
    ) -> str:
        """Run LangChain agent with tool tracking.

        Args:
            input: User input
            run_id: Evaluation run ID
            agent_id: Agent ID
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        # Run the agent
        response = await self._invoke_agent(input, run_id, **kwargs)

        # Extract output
        if hasattr(response, 'output'):
            return response.output
        elif isinstance(response, dict):
            return response.get('output', str(response))
        else:
            return str(response)

    @trace_service.observe_tool(name="langchain_tool_execution")
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        run_id: str,
        **kwargs
    ) -> Any:
        """Execute a LangChain tool with trace capture.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            run_id: Run ID for tracing
            **kwargs: Additional arguments

        Returns:
            Tool execution result
        """
        # Find the tool
        tool = None
        for t in self.tools:
            if t.name == tool_name:
                tool = t
                break

        if not tool:
            raise ValueError(f"Tool {tool_name} not found")

        # Execute the tool
        if hasattr(tool, 'ainvoke'):
            result = await tool.ainvoke(tool_input, **kwargs)
        elif hasattr(tool, 'arun'):
            result = await tool.arun(tool_input, **kwargs)
        else:
            # Fallback to sync
            if hasattr(tool, 'invoke'):
                result = tool.invoke(tool_input, **kwargs)
            else:
                result = tool.run(tool_input, **kwargs)

        return result


class LangChainAgentAdapterWithCallbacks(LangChainAgentAdapter):
    """LangChain adapter with callback-based tracing."""

    def __init__(self, agent, callbacks: Optional[List] = None):
        """Initialize with callbacks.

        Args:
            agent: LangChain agent instance
            callbacks: List of LangChain callbacks
        """
        super().__init__(agent)
        self.callbacks = callbacks or []

    @trace_service.observe_agent(name="langchain_agent_with_callbacks")
    async def run(
        self,
        input: str,
        run_id: str,
        agent_id: str,
        **kwargs
    ) -> str:
        """Run LangChain agent with callbacks.

        Args:
            input: User input
            run_id: Evaluation run ID
            agent_id: Agent ID
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        # Add callbacks to kwargs
        if self.callbacks:
            kwargs['callbacks'] = self.callbacks

        # Run the agent
        response = await self._invoke_agent(input, run_id, **kwargs)

        # Extract output
        if hasattr(response, 'output'):
            return response.output
        elif isinstance(response, dict):
            return response.get('output', str(response))
        else:
            return str(response)

    @trace_service.observe_llm(name="langchain_llm_with_callbacks")
    async def _invoke_agent(
        self,
        input: str,
        run_id: str,
        **kwargs
    ) -> Any:
        """Invoke LangChain agent with callbacks.

        Args:
            input: User input
            run_id: Run ID for tracing
            **kwargs: Additional parameters

        Returns:
            Agent response
        """
        # Invoke with callbacks
        if hasattr(self.agent, 'ainvoke'):
            response = await self.agent.ainvoke(
                {"input": input},
                config={"callbacks": kwargs.get('callbacks', [])},
                **{k: v for k, v in kwargs.items() if k != 'callbacks'}
            )
        elif hasattr(self.agent, 'arun'):
            response = await self.agent.arun(
                input,
                callbacks=kwargs.get('callbacks', []),
                **{k: v for k, v in kwargs.items() if k != 'callbacks'}
            )
        else:
            # Fallback to sync
            if hasattr(self.agent, 'invoke'):
                response = self.agent.invoke(
                    {"input": input},
                    config={"callbacks": kwargs.get('callbacks', [])},
                    **{k: v for k, v in kwargs.items() if k != 'callbacks'}
                )
            else:
                response = self.agent.run(
                    input,
                    callbacks=kwargs.get('callbacks', []),
                    **{k: v for k, v in kwargs.items() if k != 'callbacks'}
                )

        return response
