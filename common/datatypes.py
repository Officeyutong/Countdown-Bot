from dataclasses import dataclass


@dataclass
class PluginMeta:
    author: str
    version: float
    description: str
