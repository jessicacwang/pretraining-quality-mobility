from dataclasses import dataclass, field

@dataclass
class UnifiedText:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)