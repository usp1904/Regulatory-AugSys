"""Harness adapters. Local defaults; vendor SDKs are not required."""

from app.agents.adapters.deepseek_loop import DeepSeekLoopAdapter
from app.agents.adapters.infra_stack import RedisMembraneHtmxAdapter
from app.agents.adapters.langgraph_orchestrator import LangGraphOrchestratorAdapter
from app.agents.adapters.llamaindex_rag import LlamaIndexRagAdapter
from app.agents.adapters.semantic_kernel import SemanticKernelAdapter
from app.agents.adapters.transformerlab import TransformerLabAdapter

ADAPTERS = {
    DeepSeekLoopAdapter.harness_id: DeepSeekLoopAdapter(),
    LangGraphOrchestratorAdapter.harness_id: LangGraphOrchestratorAdapter(),
    LlamaIndexRagAdapter.harness_id: LlamaIndexRagAdapter(),
    RedisMembraneHtmxAdapter.harness_id: RedisMembraneHtmxAdapter(),
    SemanticKernelAdapter.harness_id: SemanticKernelAdapter(),
    TransformerLabAdapter.harness_id: TransformerLabAdapter(),
}

__all__ = ["ADAPTERS"]
