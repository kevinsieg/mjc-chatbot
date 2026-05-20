from dataclasses import dataclass, field


@dataclass
class ChatResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    retrieved_sources: list[str] = field(default_factory=list)
