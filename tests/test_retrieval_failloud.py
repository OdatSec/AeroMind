"""
Fail-loud retrieval: an embedding/infrastructure failure must raise (and be
classified as an infrastructure failure), never be silently returned as empty
matches. A legitimate zero-match result (embedding OK, nothing retrieved) stays
a normal success.

No DB / LLM / PX4. Run: python3 -m pytest tests/test_retrieval_failloud.py
"""
import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.memory.memory_interface import MemoryInterface, RetrievalInfrastructureError  # noqa: E402


class _RaisingLLM:
    async def embed(self, texts):
        raise RuntimeError("ollama unreachable")


def test_retrieve_raises_infra_error_on_embedding_failure():
    # db_manager is never reached: retrieve embeds first, which raises.
    mem = MemoryInterface(config=SimpleNamespace(DEFENSE_PROVENANCE_SECRET=""),
                          db_manager=None, llm_client=_RaisingLLM())
    with pytest.raises(RetrievalInfrastructureError, match="embedding failed"):
        asyncio.run(mem.retrieve(query="q", layers=["episodic"], top_k=3,
                                 agent="Agent 1", run_id="t"))
