from typing import Optional
from datetime import datetime

from .github_service import GitHubService
from ..config import settings
from ..database import SessionLocal, Workflow, PullRequest, CheckRun, Diff, Artifact
from ..utils.logger import logger


def _get_db():
    return SessionLocal()


def refresh_pr_and_checks(workflow_id: int) -> None:
    db = _get_db()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            logger.warning(f"refresh_pr_and_checks: workflow {workflow_id} not found")
            return

        gh = GitHubService(use_real=settings.use_real_github)
        pr_data = gh.get_workflow_pr(workflow)
        if pr_data:
            pr_row = db.query(PullRequest).filter(PullRequest.workflow_id == workflow_id, PullRequest.pr_number == pr_data.get('number')).first()
            if not pr_row:
                pr_row = PullRequest(workflow_id=workflow_id)
            pr_row.pr_number = pr_data.get('number')
            pr_row.url = pr_data.get('url') or pr_data.get('html_url')
            pr_row.title = pr_data.get('title')
            pr_row.state = pr_data.get('state')
            pr_row.head_branch = pr_data.get('head_branch') or pr_data.get('head', {}).get('ref')
            pr_row.base_branch = pr_data.get('base_branch') or pr_data.get('base', {}).get('ref')
            pr_row.head_sha = pr_data.get('head_sha') or pr_data.get('head', {}).get('sha')
            pr_row.created_at = pr_data.get('created_at') or datetime.utcnow()
            pr_row.merged_at = pr_data.get('merged_at')
            db.add(pr_row)
            db.commit()
            db.refresh(pr_row)

            # Checks
            checks = gh.list_check_runs_for_pr(workflow, pr_row.pr_number)
            for chk in checks or []:
                row = CheckRun(
                    workflow_id=workflow_id,
                    pr_id=pr_row.id,
                    name=chk.get('name'),
                    status=chk.get('status'),
                    conclusion=chk.get('conclusion'),
                    html_url=chk.get('html_url') or chk.get('url'),
                    started_at=chk.get('started_at'),
                    completed_at=chk.get('completed_at')
                )
                db.add(row)
            db.commit()
    except Exception as ex:
        logger.exception(f"refresh_pr_and_checks failed for workflow {workflow_id}: {ex}")
    finally:
        db.close()


def refresh_diffs(workflow_id: int) -> None:
    db = _get_db()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            logger.warning(f"refresh_diffs: workflow {workflow_id} not found")
            return
        gh = GitHubService(use_real=settings.use_real_github)
        diffs = gh.get_workflow_diffs(workflow)
        for d in diffs or []:
            row = Diff(
                workflow_id=workflow_id,
                path=d.get('path'),
                patch=d.get('patch') or '',
                head_sha=d.get('head_sha'),
                base_sha=d.get('base_sha'),
            )
            db.add(row)
        db.commit()
    except Exception as ex:
        logger.exception(f"refresh_diffs failed for workflow {workflow_id}: {ex}")
    finally:
        db.close()


def refresh_artifacts(workflow_id: int) -> None:
    db = _get_db()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            logger.warning(f"refresh_artifacts: workflow {workflow_id} not found")
            return
        gh = GitHubService(use_real=settings.use_real_github)
        arts = gh.list_workflow_artifacts(workflow)
        for a in arts or []:
            row = Artifact(
                workflow_id=workflow_id,
                kind=a.get('kind') or 'artifact',
                uri=a.get('uri') or a.get('archive_download_url'),
                checksum=a.get('checksum'),
                size_bytes=a.get('size_in_bytes') or a.get('size'),
            )
            db.add(row)
        db.commit()
    except Exception as ex:
        logger.exception(f"refresh_artifacts failed for workflow {workflow_id}: {ex}")
    finally:
        db.close()


