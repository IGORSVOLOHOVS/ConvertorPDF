from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass
class Document:
    path: Path
    status: str = "pending"

class IConverter(Protocol):
    def convert(self, doc_path: Path, output_dir: Path) -> bool: ...