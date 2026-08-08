"""Pre-built OpenAI agent adapter with trace capture."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from app.models.trace import Trace, Span, TokenUsage
from app.services.tracing import trace_service


class OpenAIAgentAdapter:
    """Adapter for OpenAI agents with automatic trace capture."""

    def __init__(self, client, model: str = "gpt-4"):
        """Initialize OpenAI adapter.

        Args:
            client: OpenAI client instance
            model: Model name to use
        """
        self.client = client
        self.model = model

    @trace_service.observe_agent(name="openai_agent")
    async def run(
        self,
        input: str,
        run_id: str,
        agent_id: str,
        **kwargs
    ) -> str:
        """Run agent with input and capture trace.

        Args:
            input: User input
            run_id: Evaluation run ID
            agent_id: Agent ID
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        # Get messages from kwargs or create new conversation
        messages = kwargs.get('messages', [])
        if not messages:
            messages = [{"role": "user", "content": input}]

        # Call OpenAI with LLM observation
        response = await self._call_openai(messages, run_id, **kwargs)

        # Extract response content
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        elif isinstance(response, dict):
            return response.get('content', str(response))
        else:
            return str(response)

    @trace_service.observe_llm(name="openai_llm_call")
    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        run_id: str,
        **kwargs
    ) -> Any:
        """Call OpenAI API with trace capture.

        Args:
            messages: Conversation messages
            run_id: Run ID for tracing
            **kwargs: Additional API parameters

        Returns:
            OpenAI API response
        """
        # Prepare API call parameters
        params = {
            "model": self.model,
            "messages": messages,
        }

        # Add optional parameters
        if 'temperature' in kwargs:
            params['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            params['max_tokens'] = kwargs['max_tokens']
        if 'tools' in kwargs:
            params['tools'] = kwargs['tools']

        # Make API call
        response = await self.client.chat.completions.create(**params)

        return response

    @trace_service.observe_tool(name="openai_tool_call")
    async def call_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        run_id: str,
        **kwargs
    ) -> Any:
        """Call a tool with trace capture.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            run_id: Run ID for tracing
            **kwargs: Additional arguments

        Returns:
            Tool execution result
        """
        # This is a placeholder for tool execution
        # In a real implementation, this would call the actual tool
        return {"result": f"Tool {tool_name} executed", "input": tool_input}


class OpenAIAgentAdapterWithTools(OpenAIAgentAdapter):
    """OpenAI adapter with tool/function calling support."""

    def __init__(self, client, model: str = "gpt-4", tools: Optional[List[Dict]] = None):
        """Initialize with tools.

        Args:
            client: OpenAI client instance
            model: Model name
            tools: List of tool definitions
        """
        super().__init__(client, model)
        self.tools = tools or []

    @trace_service.observe_agent(name="openai_agent_with_tools")
    async def run(
        self,
        input: str,
        run_id: str,
        agent_id: str,
        **kwargs
    ) -> str:
        """Run agent with tool calling support.

        Args:
            input: User input
            run_id: Evaluation run ID
            agent_id: Agent ID
            **kwargs: Additional arguments

        Returns:
            Agent response
        """
        messages = [{"role": "user", "content": input}]
        max_iterations = kwargs.get('max_iterations', 10)
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call OpenAI with tools
            response = await self._call_openai_with_tools(messages, run_id, **kwargs)

            # Check if response has tool calls
            if hasattr(response, 'choices') and response.choices:
                message = response.choices[0].message

                # If no tool calls, return the content
                if not message.tool_calls:
                    return message.content

                # Add assistant message with tool calls
                messages.append(message)

                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_result = await self._execute_tool_call(
                        tool_call,
                        run_id,
                        **kwargs
                    )

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
            else:
                # No choices, return error
                return "Error: No response from OpenAI"

        return "Error: Max iterations reached"

    @trace_service.observe_llm(name="openai_llm_with_tools")
    async def _call_openai_with_tools(
        self,
        messages: List[Dict[str, str]],
        run_id: str,
        **kwargs
    ) -> Any:
        """Call OpenAI with tools enabled.

        Args:
            messages: Conversation messages
            run_id: Run ID for tracing
            **kwargs: Additional parameters

        Returns:
            OpenAI API response
        """
        params = {
            "model": self.model,
            "messages": messages,
        }

        if self.tools:
            params['tools'] = self.tools

        if 'temperature' in kwargs:
            params['temperature'] = kwargs['temperature']

        response = await self.client.chat.completions.create(**params)
        return response

    @trace_service.observe_tool(name="openai_tool_execution")
    async def _execute_tool_call(
        self,
        tool_call: Any,
        run_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a tool call from OpenAI.

        Args:
            tool_call: Tool call object from OpenAI
            run_id: Run ID for tracing
            **kwargs: Additional arguments

        Returns:
            Tool execution result
        """
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Execute the tool (placeholder implementation)
        result = {
            "tool": tool_name,
            "arguments": tool_args,
            "result": f"Executed {tool_name} with args {tool_args}"
        }

        return result
