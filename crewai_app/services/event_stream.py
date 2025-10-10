from typing import Dict, Any, Optional
from queue import Queue, Empty
from datetime import datetime

_workflow_event_queues: Dict[int, Queue] = {}

def get_event_queue(workflow_id: int) -> Queue:
    if workflow_id not in _workflow_event_queues:
        _workflow_event_queues[workflow_id] = Queue()
    return _workflow_event_queues[workflow_id]

def post_event(workflow_id: int, event: Dict[str, Any]) -> None:
    event_with_meta = dict(event)
    event_with_meta.setdefault("timestamp", datetime.utcnow().isoformat())
    q = get_event_queue(workflow_id)
    q.put(event_with_meta)

def try_get_event(workflow_id: int, timeout_seconds: float = 0.0) -> Optional[Dict[str, Any]]:
    q = get_event_queue(workflow_id)
    try:
        return q.get(timeout=timeout_seconds)
    except Empty:
        return None

