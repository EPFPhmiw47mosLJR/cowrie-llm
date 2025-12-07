# Copyright (c) 2025
# LLM-backed command handler for Cowrie

"""
This module provides a command handler that forwards unknown commands
to an LLM cache service for dynamic response generation.
"""

from __future__ import annotations

from twisted.internet import defer
from twisted.python import log

from cowrie.shell.command import HoneyPotCommand
from cowrie.core.llm_cache import get_llm_cache_client

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

commands: dict[str, Callable] = {}


class Command_llm(HoneyPotCommand):
    """
    Command handler that queries the LLM cache service for unknown commands.
    This is used as a fallback when a command is not found in the standard
    command handlers.
    """

    @defer.inlineCallbacks
    def start(self) -> None:
        """
        Start the LLM command execution.
        Queries the LLM cache service and returns the response.
        """
        # Reconstruct the full command line
        cmd_parts = [self.name] + self.args
        full_command = " ".join(cmd_parts)
        
        log.msg(f"LLM command handler invoked for: {full_command}")
        
        # Get the LLM cache client
        llm_client = get_llm_cache_client()
        
        # Query the LLM cache service
        response = yield llm_client.query_command(full_command)
        
        if response:
            # Write the LLM response to the terminal
            self.write(response)
            if not response.endswith("\n"):
                self.write("\n")
        else:
            # Fallback to standard "command not found" message
            self.write(f"bash: {self.name}: command not found\n")
        
        self.exit()

    def lineReceived(self, line: str) -> None:
        """
        Handle additional input (e.g., for interactive commands).
        For now, we don't support interactive LLM commands.
        """
        log.msg(f"LLM command received input: {line}")


# Note: We don't register this in the commands dict directly.
# Instead, it will be instantiated dynamically when a command is not found.
