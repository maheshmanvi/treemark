# === FILE: tree_mark/core/usecases/generate_structure.py ===
from typing import Optional, List
from tree_mark.factory.scanner_factory import ScannerFactory
from tree_mark.core.models.schemas import OutputFormat
from tree_mark.adapters.serializers.json_serializer import serialize_to_json
from tree_mark.adapters.serializers.markdown_serializer import serialize_to_markdown
from tree_mark.adapters.repository.file_repository import write_json_file, write_text_file
from tree_mark.core.models.usecase_result import UseCaseResult
from loguru import logger

from tree_mark.utils.timeit import timeit_async


class GenerateStructureUseCase:
    """Use case orchestration for generating folder structures.

    It is intentionally thin: orchestration logic only. Business rules live in adapters and core models.
    """
    def __init__(self, scanner_kind: str = 'auto', max_concurrency: int = 10):
        self.scanner_kind = scanner_kind
        self.max_concurrency = max_concurrency

    # # async def generate(self, path: str, include_extensions: Optional[List[str]] = None, exclude_extensions: Optional[List[str]] = None, output: OutputFormat = OutputFormat.BOTH, out_prefix: str = 'treemark_out'):
    # @timeit_async
    # async def generate(
    #         self,
    #         path: str,
    #         include_extensions: Optional[list[str]] = None,
    #         exclude_extensions: Optional[list[str]] = None,
    #         output: OutputFormat = OutputFormat.BOTH,
    #         outputs_dir: str = "outputs"
    # ):
    #     logger.info("Starting generate for path={}", path)
    #     scanner = ScannerFactory.get_scanner(path, kind=self.scanner_kind, max_concurrency=self.max_concurrency)
    #     tree = await scanner.scan(path, include_extensions, exclude_extensions)
    #
    #     # create outputs directory
    #     outputs_dir = ensure_outputs_dir(outputs_dir)
    #
    #     # build a friendly filename based on path
    #     safe_name = sanitize_path_for_filename(path)
    #
    #     results = {}
    #     if output in (OutputFormat.JSON, OutputFormat.BOTH):
    #         json_obj = await serialize_to_json(tree)
    #         json_path = os.path.join(outputs_dir, f"{safe_name}.json")
    #         await write_json_file(json_path, json_obj)
    #         results['json'] = json_path
    #         logger.info("Wrote JSON to {}", json_path)
    #
    #     if output in (OutputFormat.MARKDOWN, OutputFormat.BOTH):
    #         md_text = await serialize_to_markdown(tree)
    #         md_path = os.path.join(outputs_dir, f"{safe_name}.md")
    #         await write_text_file(md_path, md_text)
    #         results['markdown'] = md_path
    #         logger.info("Wrote Markdown to {}", md_path)
    #
    #     return results

    # new signature: add keep_extensions param (default True)
    @timeit_async
    async def generate(
            self,
            path: str,
            include_extensions: Optional[list[str]] = None,
            exclude_extensions: Optional[list[str]] = None,
            output: OutputFormat = OutputFormat.BOTH,
            outputs_dir: str = "outputs",
            keep_extensions: bool = True,
    ) -> UseCaseResult:
        logger.info("Starting generate for path={}", path)
        scanner = ScannerFactory.get_scanner(path, kind=self.scanner_kind, max_concurrency=self.max_concurrency)
        tree = await scanner.scan(path, include_extensions, exclude_extensions)

        # Prepare outputs directory and friendly filename
        import os
        from tree_mark.utils.io_helpers import ensure_outputs_dir, sanitize_path_for_filename

        outputs_dir = ensure_outputs_dir(outputs_dir)
        safe_name = sanitize_path_for_filename(path)

        results = {}
        if output in (OutputFormat.JSON, OutputFormat.BOTH):
            json_obj = await serialize_to_json(tree, keep_extensions=keep_extensions)
            json_path = os.path.join(outputs_dir, f"{safe_name}.json")
            await write_json_file(json_path, json_obj)
            results['json'] = json_path
            logger.info("Wrote JSON to {}", json_path)

        if output in (OutputFormat.MARKDOWN, OutputFormat.BOTH):
            md_text = await serialize_to_markdown(tree, keep_extensions=keep_extensions)
            md_path = os.path.join(outputs_dir, f"{safe_name}.md")
            await write_text_file(md_path, md_text)
            results['markdown'] = md_path
            logger.info("Wrote Markdown to {}", md_path)

        return results
