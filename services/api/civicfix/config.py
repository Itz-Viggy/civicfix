from pathlib import Path
import os, tomllib
from pydantic import BaseModel, ConfigDict, Field
ROOT=Path(__file__).resolve().parents[3]
class Config(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: int = Field(default=1,ge=1,le=1)
    mode: str = 'real'
    data_dir: str = str(ROOT/'.runtime/app')
    allowed_origins: list[str] = ['http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8000','http://localhost:8000']
    cleanup_interval: int = Field(default=60,ge=1,le=60)
    analysis_timeout: int = Field(default=60,ge=1,le=120)
    def validate_mode(self):
        if self.mode not in ('real','fixture'): raise ValueError('Unsupported mode')
        if any(x not in ('http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8000','http://localhost:8000') for x in self.allowed_origins):
            raise ValueError('Only local origins supported')
        return self

def load_config(data_dir=None,mode=None):
    values={}
    if path:=os.getenv('CIVICFIX_CONFIG'):
        values=tomllib.loads(Path(path).read_text())
    if data_dir or os.getenv('CIVICFIX_DATA_DIR'): values['data_dir']=str(data_dir or os.environ['CIVICFIX_DATA_DIR'])
    if mode or os.getenv('CIVICFIX_MODE'): values['mode']=mode or os.environ['CIVICFIX_MODE']
    return Config(**values).validate_mode()
