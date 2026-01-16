"""
Ingestion CLI for Knowledge Graph pipeline.

Usage:
    python -m app.ingest.cli --steps embed_chunks,upsert_qdrant
    python -m app.ingest.cli --steps all --dry-run
    python -m app.ingest.cli --resume-from chunk_tafsir
    python -m app.ingest.cli --since last_success
"""

import argparse
import asyncio
import logging
import sys
from typing import List, Optional

from app.ingest.orchestrator import (
    IngestOrchestrator,
    StepName,
    get_orchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_steps(steps_arg: str) -> List[str]:
    """Parse step names from comma-separated string."""
    if steps_arg.lower() == "all":
        return [s.value for s in StepName]

    steps = []
    for step in steps_arg.split(","):
        step = step.strip()
        # Validate step name
        valid_names = [s.value for s in StepName]
        if step not in valid_names:
            logger.warning(f"Unknown step: {step}. Valid steps: {valid_names}")
            continue
        steps.append(step)

    return steps


async def run_pipeline(
    steps: List[str],
    dry_run: bool = False,
    resume_from: Optional[str] = None,
    since_last_success: bool = False,
    config: dict = None,
) -> None:
    """Execute the ingestion pipeline."""
    orchestrator = get_orchestrator()

    # If --since last_success, find resume point
    if since_last_success:
        last_run = await orchestrator.get_last_successful_run()
        if last_run and last_run.steps_completed:
            last_step = last_run.steps_completed[-1]
            # Find next step after last completed
            all_steps = [s.value for s in StepName]
            try:
                idx = all_steps.index(last_step)
                if idx + 1 < len(all_steps):
                    resume_from = all_steps[idx + 1]
                    logger.info(f"Last successful run completed: {last_step}")
                    logger.info(f"Resuming from: {resume_from}")
                else:
                    logger.info("All steps already completed in last run")
                    return
            except ValueError:
                pass

    logger.info("=" * 60)
    logger.info("TADABBUR KNOWLEDGE GRAPH INGESTION")
    logger.info("=" * 60)

    if dry_run:
        logger.info("MODE: DRY RUN (no changes will be made)")
    else:
        logger.info("MODE: LIVE RUN")

    logger.info(f"Steps: {steps}")
    if resume_from:
        logger.info(f"Resume from: {resume_from}")
    logger.info("=" * 60)

    try:
        run = await orchestrator.execute_run(
            steps=steps,
            config=config or {},
            dry_run=dry_run,
            resume_from=resume_from,
        )

        if run:
            logger.info("=" * 60)
            logger.info("RUN COMPLETED")
            logger.info(f"Run ID: {run.run_id}")
            logger.info(f"Status: {run.status.value}")
            logger.info(f"Steps completed: {run.steps_completed}")
            logger.info("=" * 60)
        else:
            logger.info("Dry run complete - no changes made")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


async def show_status() -> None:
    """Show current pipeline status."""
    orchestrator = get_orchestrator()

    logger.info("=" * 60)
    logger.info("PIPELINE STATUS")
    logger.info("=" * 60)

    last_run = await orchestrator.get_last_successful_run()
    if last_run:
        logger.info(f"Last successful run: {last_run.run_id}")
        logger.info(f"  Started: {last_run.started_at}")
        logger.info(f"  Finished: {last_run.finished_at}")
        logger.info(f"  Steps: {last_run.steps_completed}")
        logger.info(f"  Git SHA: {last_run.git_sha}")
    else:
        logger.info("No successful runs found")

    logger.info("=" * 60)
    logger.info("Available steps:")
    for step in StepName:
        logger.info(f"  - {step.value}")
    logger.info("=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tadabbur Knowledge Graph Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all steps
  python -m app.ingest.cli --steps all

  # Run specific steps
  python -m app.ingest.cli --steps embed_chunks,upsert_qdrant

  # Dry run to see planned actions
  python -m app.ingest.cli --steps all --dry-run

  # Resume from a specific step
  python -m app.ingest.cli --steps all --resume-from chunk_tafsir

  # Resume from after last successful run
  python -m app.ingest.cli --steps all --since last_success

  # Show pipeline status
  python -m app.ingest.cli --status
        """,
    )

    parser.add_argument(
        "--steps",
        type=str,
        help="Comma-separated list of steps to run, or 'all'",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without executing",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        help="Step name to resume from",
    )
    parser.add_argument(
        "--since",
        type=str,
        choices=["last_success"],
        help="Resume from after last successful run",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show pipeline status",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.status:
        asyncio.run(show_status())
        return

    if not args.steps:
        parser.print_help()
        sys.exit(1)

    steps = parse_steps(args.steps)
    if not steps:
        logger.error("No valid steps specified")
        sys.exit(1)

    asyncio.run(
        run_pipeline(
            steps=steps,
            dry_run=args.dry_run,
            resume_from=args.resume_from,
            since_last_success=args.since == "last_success",
        )
    )


if __name__ == "__main__":
    main()
