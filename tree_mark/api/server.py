# === FILE: tree_mark/api/server.py ===
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from tree_mark.core.usecases.generate_structure import GenerateStructureUseCase
from tree_mark.core.models.schemas import OutputFormat
from loguru import logger

from tree_mark.core.models.usecase_result import UseCaseResult

app = FastAPI(title="TreeMark API")

class GenerateRequest(BaseModel):
    path: str
    include_extensions: Optional[List[str]] = None
    exclude_extensions: Optional[List[str]] = None
    output: OutputFormat = OutputFormat.BOTH
    concurrency: int = 10

@app.post('/generate')
async def api_generate(req: GenerateRequest):
    try:
        usecase = GenerateStructureUseCase(max_concurrency=req.concurrency)
        # (results, elapsed) = await usecase.generate(req.path, req.include_extensions, req.exclude_extensions, req.output)
        # return {"results": results, "elapsed": elapsed}
        res = await usecase.generate(req.path, req.include_extensions, req.exclude_extensions, req.output, outputs_dir='outputs')
        if isinstance(res, UseCaseResult):
            return {"results": res.results, "elapsed": res.elapsed}
    except Exception as exc:
        logger.exception("API generate failed")
        raise HTTPException(status_code=500, detail=str(exc))