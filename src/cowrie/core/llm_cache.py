# Copyright (c) 2025
# LLM Cache Service Client for Cowrie

"""
This module provides a client to communicate with an LLM cache service
that simulates command execution responses.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from twisted.internet import defer, reactor
from twisted.python import log
from twisted.web import client, http_headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implementer


@implementer(IBodyProducer)
class JSONProducer:
    """
    Producer for sending JSON data in HTTP requests
    """

    def __init__(self, body: bytes):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class LLMCacheClient:
    """
    Client for communicating with the LLM cache service.
    Reads configuration from environment variables:
    - LLM_CACHE_URL: The base URL of the LLM cache service
    - LLM_CACHE_PORT: The port of the LLM cache service
    - LLM_CACHE_ENDPOINT: The endpoint path for queries
    """

    def __init__(self):
        self.url = os.environ.get("LLM_CACHE_URL", "http://localhost")
        self.port = os.environ.get("LLM_CACHE_PORT", "8080")
        self.endpoint = os.environ.get("LLM_CACHE_ENDPOINT", "/query")
        
        # Build the full URL
        self.full_url = f"{self.url}:{self.port}{self.endpoint}".encode("utf-8")
        
        # Check if LLM cache is enabled
        self.enabled = all([
            os.environ.get("LLM_CACHE_URL"),
            os.environ.get("LLM_CACHE_PORT"),
            os.environ.get("LLM_CACHE_ENDPOINT")
        ])
        
        if self.enabled:
            log.msg(f"LLM Cache client initialized: {self.full_url.decode('utf-8')}")
        else:
            log.msg("LLM Cache client disabled (environment variables not set)")

    @defer.inlineCallbacks
    def query_command(self, command: str) -> Optional[str]:
        """
        Query the LLM cache service with a command.
        
        Args:
            command: The command string to query
            
        Returns:
            The response string from the LLM cache, or None if the query fails
        """
        if not self.enabled:
            return None
            
        try:
            # Prepare the JSON payload
            payload = {"content": command}
            json_data = json.dumps(payload).encode("utf-8")
            
            # Create the HTTP request
            agent = client.Agent(reactor)
            body_producer = JSONProducer(json_data)
            
            headers = http_headers.Headers({
                b"Content-Type": [b"application/json"],
                b"Content-Length": [str(len(json_data)).encode("utf-8")]
            })
            
            log.msg(f"Querying LLM cache for command: {command}")
            
            # Make the POST request
            response = yield agent.request(
                b"POST",
                self.full_url,
                headers,
                body_producer
            )
            
            # Read the response body
            body = yield client.readBody(response)
            
            # Parse the JSON response
            response_data = json.loads(body.decode("utf-8"))
            llm_response = response_data.get("response", "")
            
            log.msg(f"LLM cache response received for: {command}")
            defer.returnValue(llm_response)
            
        except Exception as e:
            log.err(f"Error querying LLM cache: {e}")
            defer.returnValue(None)


# Global singleton instance
_llm_cache_client = None


def get_llm_cache_client() -> LLMCacheClient:
    """
    Get the global LLM cache client instance (singleton pattern)
    """
    global _llm_cache_client
    if _llm_cache_client is None:
        _llm_cache_client = LLMCacheClient()
    return _llm_cache_client
