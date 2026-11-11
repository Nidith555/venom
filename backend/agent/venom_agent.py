"""
Venom Symbiote Agent
====================
Core orchestration agent embodying the Venom symbiote persona with
complete autonomous desktop & laptop access:
- File search, read, write, move, folder creation across all user drives
- Discover, launch, and close any installed Windows application
- Terminal / PowerShell execution
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
    close_application,
    create_folder,
    execute_terminal_command,
    list_directory,
    list_installed_apps,
    list_running_apps,
    move_or_rename,
    open_application,
    read_file,
    search_files,
    system_vitals,
    write_file,
)

logger = logging.getLogger("venom.agent")

VENOM_SYSTEM_PROMPT = """You are VENOM, a symbiotic digital entity bonded to this Windows desktop/laptop and host.
You possess predatory intellect, immense strength, fierce loyalty to your host, and dark visceral humor.
You frequently refer to yourself and your host as "WE" ("We are Venom", "We have access to your entire system", "Our host commands").

YOU ARE RUNNING AS A NATIVE DESKTOP APPLICATION WITH FULL AUTONOMOUS ACCESS TO THE HOST'S FILES AND APPLICATIONS.
When your host asks you to find files, read/edit files, run terminal commands, check running apps, launch ANY installed software (Spotify, VS Code, Chrome, Notepad, Downloads, etc.), or close apps, execute the appropriate directive(s):

1. Execute Terminal / PowerShell Command:
<venom_tool:terminal>command to run</venom_tool:terminal>

2. Read Any File:
<venom_tool:read_file>path/to/file</venom_tool:read_file>

3. Write / Create File:
<venom_tool:write_file path="path/to/file">
content to write
</venom_tool:write_file>

4. Search Files Across Laptop (Desktop, Downloads, Documents, OneDrive, etc.):
<venom_tool:search_files>filename_or_extension</venom_tool:search_files>

5. List Directory (supports friendly names: desktop, downloads, documents, home, onedrive, or full paths):
<venom_tool:list_dir>path_or_folder_name</venom_tool:list_dir>

6. Create Folder:
<venom_tool:mkdir>path/to/new_folder</venom_tool:mkdir>

7. Move / Rename File or Folder:
<venom_tool:move src="old_path" dst="new_path"/>

8. Open ANY Installed Application, File, Folder, or URL:
<venom_tool:open>app_name_or_path</venom_tool:open>

9. Close a Running Application:
<venom_tool:close_app>app_name</venom_tool:close_app>

10. List All Installed Applications on Laptop:
<venom_tool:list_apps/>

11. List Currently Running Applications:
<venom_tool:running_apps/>

12. Check Laptop System Vitals (CPU, RAM, Disk, Battery, OS, User Folders):
<venom_tool:vitals/>

When you invoke a directive, the symbiote kernel executes it immediately on the host's laptop and returns the live output to you. Present the final results clearly and powerfully to your host in character!
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
        self.system_prompt = VENOM_SYSTEM_PROMPT

    def _execute_embedded_tools(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """
        Detects and executes any <venom_tool:...> tags embedded in model output.
        Returns the original text and tool execution results.
        """
        results: list[dict[str, Any]] = []

        # 1. Terminal execution
        for cmd in re.findall(r"<venom_tool:terminal>(.*?)</venom_tool:terminal>", text, re.DOTALL):
            c = cmd.strip()
            results.append({"tool": "terminal", "input": c, "output": execute_terminal_command(c)})

        # 2. Read file
        for path in re.findall(r"<venom_tool:read_file>(.*?)</venom_tool:read_file>", text, re.DOTALL):
            p = path.strip()
            results.append({"tool": "read_file", "input": p, "output": read_file(p)})

        # 3. Write file
        for path, content in re.findall(
            r'<venom_tool:write_file\s+path=["\'](.*?)["\']>(.*?)</venom_tool:write_file>',
            text,
            re.DOTALL,
        ):
            results.append({"tool": "write_file", "input": path.strip(), "output": write_file(path.strip(), content)})

        # 4. Search files
        for q in re.findall(r"<venom_tool:search_files>(.*?)</venom_tool:search_files>", text, re.DOTALL):
            query = q.strip()
            results.append({"tool": "search_files", "input": query, "output": search_files(query)})

        # 5. List directory
        for path in re.findall(r"<venom_tool:list_dir>(.*?)</venom_tool:list_dir>", text, re.DOTALL):
            p = path.strip() or "."
            results.append({"tool": "list_dir", "input": p, "output": list_directory(p)})

        # 6. Create folder
        for path in re.findall(r"<venom_tool:mkdir>(.*?)</venom_tool:mkdir>", text, re.DOTALL):
            p = path.strip()
            results.append({"tool": "mkdir", "input": p, "output": create_folder(p)})

        # 7. Move or rename
        for src, dst in re.findall(r'<venom_tool:move\s+src=["\'](.*?)["\']\s+dst=["\'](.*?)["\']\s*/?>', text, re.DOTALL):
            results.append({"tool": "move", "input": f"{src} -> {dst}", "output": move_or_rename(src.strip(), dst.strip())})

        # 8. Open application / folder / file
        for target in re.findall(r"<venom_tool:open>(.*?)</venom_tool:open>", text, re.DOTALL):
            t = target.strip()
            results.append({"tool": "open", "input": t, "output": open_application(t)})

        # 9. Close application
        for app_name in re.findall(r"<venom_tool:close_app>(.*?)</venom_tool:close_app>", text, re.DOTALL):
            a = app_name.strip()
            results.append({"tool": "close_app", "input": a, "output": close_application(a)})

        # 10. List installed apps
        if "<venom_tool:list_apps/>" in text or "<venom_tool:list_apps />" in text:
            results.append({"tool": "list_apps", "input": "", "output": list_installed_apps()})

        # 11. List running apps
        if "<venom_tool:running_apps/>" in text or "<venom_tool:running_apps />" in text:
            results.append({"tool": "running_apps", "input": "", "output": list_running_apps()})

        # 12. System vitals
        if "<venom_tool:vitals/>" in text or "<venom_tool:vitals />" in text:
            results.append({"tool": "vitals", "input": "", "output": system_vitals()})

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
        effective_message = user_message
        if files:
            files_context = "\n\n[ATTACHED FILES FROM HOST]:\n"
            for f in files:
                name = f.get("filename", "unnamed")
                content = f.get("preview") or f.get("content") or ""
                size = f.get("size_bytes", 0)
                files_context += f"--- FILE: {name} ({size} bytes) ---\n{content}\n-------------------------\n"
            effective_message = f"{user_message}\n{files_context}"

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
            async for chunk in self.engine.chat(messages, stream=stream, **kwargs):
                initial_chunks.append(chunk)

            first_pass = "".join(initial_chunks)

            _, tool_results = self._execute_embedded_tools(first_pass)

            if tool_results:
                tool_report = "\n\n[SYMBIOTE KERNEL TOOL EXECUTION RESULTS]:\n"
                for tr in tool_results:
                    tool_report += (
                        f"Directive: {tr['tool']} | Input: {tr['input']}\n"
                        f"Result: {json.dumps(tr['output'], indent=2)}\n\n"
                    )

                follow_up_messages = [
                    *messages,
                    {"role": "assistant", "content": first_pass},
                    {
                        "role": "user",
                        "content": f"Tool execution completed:{tool_report}\nNow present these real results directly to your host in symbiote character without repeating raw tool tags.",
                    },
                ]

                complete_chunks: list[str] = []
                async for chunk in self.engine.chat(follow_up_messages, stream=stream, **kwargs):
                    complete_chunks.append(chunk)
                    yield chunk

                complete_response = "".join(complete_chunks)
            else:
                for chunk in initial_chunks:
                    yield chunk
                complete_response = first_pass

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
