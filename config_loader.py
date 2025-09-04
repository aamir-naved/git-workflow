import yaml
from pydantic import BaseModel
from typing import List, Literal

class AutoSyncConfig(BaseModel):
    branches: List[str]
    strategy: Literal["merge", "rebase"]

def load_config(path: str = ".autosync.yml") -> AutoSyncConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return AutoSyncConfig(**data)
