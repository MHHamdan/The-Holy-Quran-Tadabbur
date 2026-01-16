"""
Ingestion Orchestrator for Knowledge Graph.

Manages ingestion runs with:
- Step tracking and metrics
- Idempotent processing via content hashing
- Resume capability from last success
- CLI integration
"""

import logging
import hashlib
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from app.kg.client import get_kg_client, KGClient
from app.kg.models import IngestRun, IngestStep, IngestRecordState, IngestStatus, StepStatus

logger = logging.getLogger(__name__)


class StepName(str, Enum):
    """Known ingestion step names."""
    INGEST_SOURCES = "ingest_sources"
    NORMALIZE_AYAH = "normalize_ayah"
    CHUNK_TAFSIR = "chunk_tafsir"
    EMBED_CHUNKS = "embed_chunks"
    UPSERT_QDRANT = "upsert_qdrant"
    BUILD_KG_EDGES = "build_kg_edges"
    BUILD_STORY_EVENTS = "build_story_events"
    VALIDATE_CONSTRAINTS = "validate_constraints"


@dataclass
class StepResult:
    """Result from executing a step."""
    success: bool
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


# Type for step functions
StepFunction = Callable[[KGClient, str, Dict[str, Any]], Awaitable[StepResult]]


class IngestOrchestrator:
    """
    Orchestrates ingestion pipeline runs.

    Features:
    - Creates ingest_run record at start
    - Tracks each step with ingest_step records
    - Updates ingest_record_state for idempotency
    - Supports resume from specific step
    - Provides dry-run mode
    """

    def __init__(self, kg_client: KGClient = None):
        self.kg_client = kg_client or get_kg_client()
        self._step_handlers: Dict[str, StepFunction] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default step handlers."""
        # These will be overridden by actual implementations
        for step in StepName:
            self._step_handlers[step.value] = self._placeholder_handler

    async def _placeholder_handler(
        self,
        kg: KGClient,
        run_id: str,
        config: Dict[str, Any],
    ) -> StepResult:
        """Placeholder for unimplemented steps."""
        logger.warning(f"Step handler not implemented, skipping")
        return StepResult(success=True, records_skipped=1)

    def register_step(self, step_name: str, handler: StepFunction):
        """Register a step handler."""
        self._step_handlers[step_name] = handler

    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        suffix = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"{timestamp}_{suffix}"

    def _get_git_sha(self) -> Optional[str]:
        """Get current git SHA if available."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _compute_config_hash(self, config: Dict[str, Any]) -> str:
        """Compute hash of configuration."""
        import json
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    async def create_run(
        self,
        steps: List[str],
        config: Dict[str, Any] = None,
    ) -> IngestRun:
        """
        Create a new ingestion run.

        Args:
            steps: List of step names to execute
            config: Configuration for this run

        Returns:
            IngestRun record
        """
        run_id = self._generate_run_id()
        config = config or {}

        run = IngestRun(
            run_id=run_id,
            started_at=datetime.utcnow(),
            git_sha=self._get_git_sha(),
            config_hash=self._compute_config_hash(config),
            status=IngestStatus.RUNNING,
            steps_planned=steps,
            steps_completed=[],
            metrics={"config": config},
        )

        # Save to SurrealDB
        await self.kg_client.upsert(
            "ingest_run",
            run_id,
            run.model_dump(exclude={"id"}),
        )

        logger.info(f"Created ingest run: {run_id}")
        return run

    async def get_run(self, run_id: str) -> Optional[IngestRun]:
        """Get an existing run by ID."""
        record = await self.kg_client.get(f"ingest_run:{run_id}")
        if record:
            return IngestRun(**record)
        return None

    async def get_last_successful_run(self) -> Optional[IngestRun]:
        """Get the most recent successful run."""
        results = await self.kg_client.select(
            "ingest_run",
            where='status = "completed"',
            order_by="started_at DESC",
            limit=1,
        )
        if results:
            return IngestRun(**results[0])
        return None

    async def start_step(self, run_id: str, step_name: str) -> IngestStep:
        """Start tracking a step."""
        step = IngestStep(
            run_id=run_id,
            step_name=step_name,
            started_at=datetime.utcnow(),
            status=StepStatus.RUNNING,
        )

        await self.kg_client.upsert(
            "ingest_step",
            f"{run_id}:{step_name}",
            step.model_dump(exclude={"id"}),
        )

        logger.info(f"Started step: {step_name}")
        return step

    async def complete_step(
        self,
        run_id: str,
        step_name: str,
        result: StepResult,
    ) -> IngestStep:
        """Mark a step as complete."""
        status = StepStatus.COMPLETED if result.success else StepStatus.FAILED

        finished_at = datetime.utcnow()
        update_data = {
            "finished_at": finished_at.isoformat(),
            "status": status.value,
            "records_processed": result.records_processed,
            "records_created": result.records_created,
            "records_updated": result.records_updated,
            "records_skipped": result.records_skipped,
            "error_message": result.error_message,
            "metrics": result.metrics,
        }

        await self.kg_client.update(
            f"ingest_step:{run_id}:{step_name}",
            update_data,
        )

        logger.info(f"Completed step: {step_name} - {status.value}")
        return IngestStep(
            run_id=run_id,
            step_name=step_name,
            started_at=finished_at,  # Placeholder - actual start time is in DB
            finished_at=finished_at,
            status=status,
            records_processed=result.records_processed,
            records_created=result.records_created,
            records_updated=result.records_updated,
            records_skipped=result.records_skipped,
            error_message=result.error_message,
            metrics=result.metrics,
        )

    async def complete_run(
        self,
        run_id: str,
        success: bool,
        error_message: str = None,
    ):
        """Mark a run as complete."""
        status = IngestStatus.COMPLETED if success else IngestStatus.FAILED

        await self.kg_client.update(
            f"ingest_run:{run_id}",
            {
                "finished_at": datetime.utcnow().isoformat(),
                "status": status.value,
                "error_message": error_message,
            },
        )

        logger.info(f"Completed run: {run_id} - {status.value}")

    async def should_skip_record(
        self,
        record_id: str,
        record_type: str,
        content_hash: str,
        step_name: str,
    ) -> bool:
        """
        Check if a record should be skipped based on hash.

        Returns True if the record has already been processed
        with the same content hash for this step.
        """
        state = await self.kg_client.get(f"ingest_record_state:{record_id}")

        if not state:
            return False

        # Check if content hash matches
        if state.get("content_hash") != content_hash:
            return False

        # Check if this step was already completed
        steps = state.get("steps", {})
        step_state = steps.get(step_name, {})

        return step_state.get("status") == "completed"

    async def update_record_state(
        self,
        record_id: str,
        record_type: str,
        content_hash: str,
        run_id: str,
        step_name: str,
        status: str,
    ):
        """Update the state of a processed record."""
        # Get existing state
        existing = await self.kg_client.get(f"ingest_record_state:{record_id}")

        steps = existing.get("steps", {}) if existing else {}
        steps[step_name] = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
        }

        state_data = {
            "record_id": record_id,
            "record_type": record_type,
            "last_run_id": run_id,
            "content_hash": content_hash,
            "steps": steps,
            "_updated_at": datetime.utcnow().isoformat(),
        }

        await self.kg_client.upsert(
            "ingest_record_state",
            record_id,
            state_data,
        )

    async def execute_run(
        self,
        steps: List[str] = None,
        config: Dict[str, Any] = None,
        dry_run: bool = False,
        resume_from: str = None,
    ) -> IngestRun:
        """
        Execute an ingestion run.

        Args:
            steps: Steps to execute (default: all steps)
            config: Configuration
            dry_run: If True, only print planned actions
            resume_from: Step name to resume from

        Returns:
            Completed IngestRun
        """
        steps = steps or [s.value for s in StepName]
        config = config or {}

        # Find resume point if specified
        if resume_from:
            try:
                idx = steps.index(resume_from)
                steps = steps[idx:]
                logger.info(f"Resuming from step: {resume_from}")
            except ValueError:
                logger.warning(f"Resume step not found: {resume_from}")

        if dry_run:
            logger.info("=== DRY RUN ===")
            logger.info(f"Planned steps: {steps}")
            logger.info(f"Config: {config}")
            return None

        # Create run record
        run = await self.create_run(steps, config)
        run_id = run.run_id

        try:
            for step_name in steps:
                # Start step tracking
                await self.start_step(run_id, step_name)

                # Get handler
                handler = self._step_handlers.get(step_name)
                if not handler:
                    logger.warning(f"No handler for step: {step_name}")
                    await self.complete_step(
                        run_id,
                        step_name,
                        StepResult(success=True, records_skipped=1),
                    )
                    continue

                # Execute step
                try:
                    result = await handler(self.kg_client, run_id, config)
                    await self.complete_step(run_id, step_name, result)

                    if not result.success:
                        raise Exception(result.error_message or "Step failed")

                    # Update run with completed step
                    await self.kg_client.update(
                        f"ingest_run:{run_id}",
                        {"steps_completed": run.steps_completed + [step_name]},
                    )
                    run.steps_completed.append(step_name)

                except Exception as e:
                    logger.error(f"Step {step_name} failed: {e}")
                    await self.complete_step(
                        run_id,
                        step_name,
                        StepResult(success=False, error_message=str(e)),
                    )
                    await self.complete_run(run_id, False, str(e))
                    raise

            # All steps completed
            await self.complete_run(run_id, True)
            return run

        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}")
            raise


# Singleton
_orchestrator: Optional[IngestOrchestrator] = None


def get_orchestrator() -> IngestOrchestrator:
    """Get or create the orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IngestOrchestrator()
    return _orchestrator
