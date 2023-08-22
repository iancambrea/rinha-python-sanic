from pydantic import BaseModel, constr, Field
from typing import Optional, List
from datetime import date
from uuid import UUID, uuid4

class PessoaBase(BaseModel):
    apelido: constr(max_length=32)
    nome: constr(max_length=100)
    nascimento: date
    stack: Optional[List[str]] = None

    @property
    def stack(self) -> str:
        return ' '.join(self.stack) if self.stack else None


class PessoaCreate(PessoaBase):
    id: UUID = Field(default_factory=uuid4)