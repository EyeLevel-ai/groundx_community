import time
import logging
from typing import Optional, Any


def upload_poller(
    client: Any,
    process_id: str,
    *,
    poll_interval: float = 2.0,
    timeout: Optional[float] = None,
    print_updates: bool = True,
    print_completed: bool = True,
    logger: Optional[logging.Logger] = None,
) -> str:
    """
    Polls a GroundX upload / ingest process until it reaches a terminal state.

    Parameters
    ----------
    client : GroundX
        An initialized GroundX client.
    process_id : str
        The upload / ingest process_id to poll.
    poll_interval : float, optional
        Seconds to sleep between polls (default: 2.0).
    timeout : float or None, optional
        Maximum time in seconds to poll before raising TimeoutError.
        If None, poll indefinitely.
    print_updates : bool, optional
        If True, prints state updates while polling (if no logger provided).
    print_completed : bool, optional
        If True, prints a completion message when finished.
    logger : logging.Logger, optional
        An optional logger instance. If provided, status updates will be 
        sent to logger.info instead of using print().

    Returns
    -------
    str
        Final ingest state.

    In-Progress States
    ------------------
    queued, processing, active, training

    Terminal States
    ---------------
    error, complete, cancelled, inactive
    """

    in_progress_states = {"queued", "processing", "active", "training"}
    terminal_states = {"error", "complete", "cancelled", "inactive"}

    start_time = time.monotonic()
    last_state = None

    # Helper for unified logging/printing
    def log_status(message: str):
        if logger:
            logger.info(message)
        elif print_updates:
            print(message)

    while True:
        # Timeout check
        if timeout is not None:
            elapsed = time.monotonic() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Polling timed out after {timeout}s for process_id={process_id}"
                )

        # GroundX API call
        response = client.documents.get_processing_status_by_id(
            process_id=process_id
        )

        ingest = response.ingest
        if not ingest:
            raise RuntimeError(
                f"Missing 'ingest' field in response for process_id={process_id}: {response}"
            )

        state = ingest.status
        if not state:
            raise RuntimeError(
                f"Missing ingest status for process_id={process_id}: {ingest}"
            )

        # Log updates only on state changes
        if state != last_state:
            log_status(f"[upload_poller] process_id={process_id} → state='{state}'")
        
        last_state = state

        # Terminal state handling
        if state in terminal_states:
            if print_completed:
                if logger:
                    logger.info(f"[upload_poller] process_id={process_id} finished with state='{state}'")
                else:
                    print(f"[upload_poller] process_id={process_id} finished with state='{state}'")
            return state

        # Safety check for unexpected states
        if state not in in_progress_states:
            raise RuntimeError(
                f"Unknown ingest state '{state}' for process_id={process_id}"
            )

        time.sleep(poll_interval)