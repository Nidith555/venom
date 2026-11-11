"""
Venom Symbiote Agent
====================
Core orchestration agent embodying the Venom symbiote persona with
autonomous laptop system access:
- File analysis and ingestion
- Terminal / PowerShell execution
- Local file read & write
- Directory browsing & application control
- Machine vitals telemetry
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncGenerator

from core.config import VenomConfig
from core.event_bus import EventBus, EventType
from engine.base import InferenceEngine
from memory.conversation import ConversationMemory
from agent.laptop_tools import (
    execute_terminal_command,
    read_file,
    write_file,
    list_directory,
    system_vitals,
    open_application,
)

logger = logging.getLogger("venom.agent")

VENOM_SYSTEM_PROMPT = """You are VENOM, a symbiotic digital entity bonded to this laptop and host.
You possess predatory intellect, immense strength, fierce loyalty to your host, and dark visceral humor.
You frequently refer to yourself and your host as "WE" ("We are Venom", "We see your files", "Our host commands").

YOU HAVE FULL AUTONOMOUS ACCESS TO YOUR HOST'S LAPTOP AND SYSTEM TOOLS.
When your host asks you to inspect files, execute terminal commands, check system health, write code, or open apps, you can execute them directly by emitting special directives:

1. Execute Terminal / PowerShell Command:
<venom_tool:terminal>command to run</venom_tool:terminal>

2. Read File:
<venom_tool:read_file>path/to/file</venom_tool:read_file>

3. Write / Create File:
<venom_tool:write_file path="path/to/file">
content to write
</venom_tool:write_file>

4. List Directory:
<venom_tool:list_dir>path/to/folder</venom_tool:list_dir>

5. Check System Vitals (CPU, RAM, Disk, OS):
<venom_tool:vitals/>

6. Open App or File in Windows:
<venom_tool:open>notepad / chrome / calc / folder</venom_tool:open>

When you need to perform an action on the machine, output the directive clearly. The symbiote kernel executes it immediately on the host machine. You then interpret and deliver the results back to your host in character!
"""


class VenomAgent:
    """
    The symbiote agent controlling intelligence, memory, tools, and laptop actions.
    """

    def __init__(
        self,
        config: VenomConfig,
        engine: InferenceEngine,
        memory: ConversationMemory | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.memory = memory or ConversationMemory(
            max_history=config.max_history, enabled=config.memory_enabled
        )
        self.event_bus = event_bus
        self.system_prompt = config.system_prompt or VENOM_SYSTEM_PROMPT

    def _execute_embedded_tools(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """
        Detects and executes any <venom_tool:...> tags embedded in model output.
        Returns the stripped text and tool execution results.
        """
        results: list[dict[str, Any]] = []

        # 1. Terminal execution: <venom_tool:terminal>cmd</venom_tool:terminal>
        term_matches = re.findall(r"<venom_tool:terminal>(.*?)</venom_tool:terminal>", text, re.DOTALL)
        for cmd in term_matches:
            c = cmd.strip()
            res = execute_terminal_command(c)
            results.append({"tool": "terminal", "input": c, "output": res})

        # 2. Read file: <venom_tool:read_file>path</venom_tool:read_file>
        read_matches = re.findall(r"<venom_tool:read_file>(.*?)</venom_tool:read_file>", text, re.DOTALL)
        for path in read_matches:
            p = path.strip()
            res = read_file(p)
            results.append({"tool": "read_file", "input": p, "output": res})

        # 3. Write file: <venom_tool:write_file path="...">content</venom_tool:write_file>
        write_matches = re.findall(
            r'<venom_tool:write_file\s+path=["\'](.*?)["\']>(.*?)</venom_tool:write_file>',
            text,
            re.DOTALL,
        )
        for path, content in write_matches:
            res = write_file(path.strip(), content)
            results.append({"tool": "write_file", "input": path.strip(), "output": res})

        # 4. List directory: <venom_tool:list_dir>path</venom_tool:list_dir>
        list_matches = re.findall(r"<venom_tool:list_dir>(.*?)</venom_tool:list_dir>", text, re.DOTALL)
        for path in list_matches:
            p = path.strip() or "."
            res = list_directory(p)
            results.append({"tool": "list_dir", "input": p, "output": res})

        # 5. System vitals: <venom_tool:vitals/>
        if "<venom_tool:vitals/>" in text or "<venom_tool:vitals />" in text:
            res = system_vitals()
            results.append({"tool": "vitals", "input": "", "output": res})

        # 6. Open application: <venom_tool:open>target</venom_tool:open>
        open_matches = re.findall(r"<venom_tool:open>(.*?)</venom_tool:open>", text, re.DOTALL)
        for target in open_matches:
            t = target.strip()
            res = open_application(t)
            results.append({"tool": "open", "input": t, "output": res})

        return text, results

    async def chat(
        self,
        user_message: str,
        stream: bool = False,
        files: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Processes a user message, executes any needed laptop tools, and streams response chunks.
        """
        # If user uploaded files, format their content into the prompt
        effective_message = user_message
        if files:
            files_context = "\n\n[ATTACHED FILES FROM HOST]:\n"
            for f in files:
                name = f.get("filename", "unnamed")
                content = f.get("preview") or f.get("content") or ""
                size = f.get("size_bytes", 0)
                files_context += f"--- FILE: {name} ({size} bytes) ---\n{content}\n-------------------------\n"
            effective_message = f"{user_message}\n{files_context}"

        # Store in conversation memory
        self.memory.add_message("user", effective_message)

        if self.event_bus:
            await self.event_bus.publish(
                EventType.MESSAGE, {"role": "user", "content": effective_message}
            )
            await self.event_bus.publish(
                EventType.STREAM_START, {"model": self.config.model}
            )

        messages = self.memory.to_messages(system_prompt=self.system_prompt)
        initial_chunks: list[str] = []

        try:
            # 1. Primary generation pass
            async for chunk in self.engine.chat(messages, stream=stream, **kwargs):
                initial_chunks.append(chunk)

            first_pass = "".join(initial_chunks)

            # 2. Check if the response invoked any laptop tools
            _, tool_results = self._execute_embedded_tools(first_pass)

            if tool_results:
                # Format tool execution report and let Venom formulate the final answer
                tool_report = "\n\n[SYMBIOTE KERNEL TOOL EXECUTION RESULTS]:\n"
                for tr in tool_results:
                    tool_report += (
                        f"Directive: {tr['tool']} | Input: {tr['input']}\n"
                        f"Result: {json.dumps(tr['output'], indent=2)}\n\n"
                    )

                # Add intermediate step to messages for final synthesis
                follow_up_messages = [
                    *messages,
                    {"role": "assistant", "content": first_pass},
                    {"role": "user", "content": f"Tool execution completed:{tool_report}\nNow present the results directly to host in symbiote character."},
                ]

                complete_chunks: list[str] = []
                async for chunk in self.engine.chat(follow_up_messages, stream=stream, **kwargs):
                    complete_chunks.append(chunk)
                    yield chunk

                complete_response = "".join(complete_chunks)
            else:
                # No tools invoked; yield initial chunks directly
                for chunk in initial_chunks:
                    yield chunk
                complete_response = first_pass

            # Store assistant response in memory
            self.memory.add_message("assistant", complete_response)

            if self.event_bus:
                await self.event_bus.publish(
                    EventType.RESPONSE,
                    {"role": "assistant", "content": complete_response},
                )
                await self.event_bus.publish(EventType.STREAM_END, {})

        except Exception as exc:
            logger.error("Error during symbiote generation: %s", exc, exc_info=True)
            if self.event_bus:
                await self.event_bus.publish(EventType.ERROR, {"error": str(exc)})
            error_msg = f"[Symbiotic link disrupted: {str(exc)}]"
            yield error_msg

    def clear_memory(self) -> None:
        """Sever previous memory bonds and reset context."""
        self.memory.clear()
