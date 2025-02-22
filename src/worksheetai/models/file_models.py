import json
from typing import List, Union, Any, Dict
from pydantic import BaseModel
from typing import Union, List, Dict, Any, Literal
from collections.abc import Mapping

class BaseFileModel(BaseModel):
    def to_file_content(self) -> str:
        """
        Convert model to file content. Should be overridden by subclasses if needed.
        """
        return self.json(indent=2)

class NotebookCell(BaseModel, Mapping):
    cell_type: Literal['markdown', 'code']
    source: Union[str, List[str]]
    metadata: Dict[str, Any] = {}

    def __getitem__(self, key):
        return self.dict()[key]

    def __iter__(self):
        return iter(self.dict())

    def __len__(self):
        return len(self.dict())

class NotebookCells(BaseModel, Mapping):
    cells: List[NotebookCell]

    def __getitem__(self, key):
        return self.dict()[key]

    def __iter__(self):
        return iter(self.dict())

    def __len__(self):
        return len(self.dict())

class IPYNBModel(BaseFileModel, Mapping):
    nbformat: int = 4
    nbformat_minor: int = 5
    metadata: Dict[str, Any] = {}
    # It’s simpler to store cells as a list.
    cells: List[NotebookCell] = []

    def __getitem__(self, key):
        return self.dict()[key]

    def __iter__(self):
        return iter(self.dict())

    def __len__(self):
        return len(self.dict())

    def to_file_content(self) -> str:
        # Now you can pass self directly to json.dumps.
        return json.dumps(self.dict(), indent=2, default=str)

class PDFModel(BaseFileModel):
    title: str
    author: str
    content: str

    def to_file_content(self) -> str:
        return f"Title: {self.title}\nAuthor: {self.author}\n\n{self.content}"