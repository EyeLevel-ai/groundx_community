import os
import logging
import pytest
from uuid import uuid4
from dotenv import load_dotenv

from groundx import GroundX, Document
from groundx_community.upload_utils.management import upload_poller

# Setup logging for the test suite
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

# Load .env from project root (one level up from /tests)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

@pytest.mark.integration
def test_upload_poller_remote_pdf():
    """
    End-to-end test:
    - Create a dynamic bucket
    - Ingest remote PDF
    - Poll until terminal state using the provided logger
    """

    api_key = os.getenv("GROUNDX_API_KEY")
    if not api_key:
        pytest.fail("GROUNDX_API_KEY not found in environment variables.")

    client = GroundX(api_key=api_key)

    # 1. Create a temporary bucket for this test run
    bucket_name = f"test-bucket-{uuid4().hex[:8]}"
    logger.info(f"Creating temporary bucket: {bucket_name}")
    
    bucket_response = client.buckets.create(name=bucket_name)
    
    # Handle both object-based and dict-based SDK responses
    if hasattr(bucket_response, 'bucket'):
        bucket_id = bucket_response.bucket.bucket_id
    else:
        bucket_id = bucket_response["bucket"]["bucketId"]
        
    logger.info(f"Bucket created with ID: {bucket_id}")

    # 2. Ingest a remote PDF
    remote_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    logger.info("Uploading remote PDF: %s", remote_pdf_url)

    ingest_response = client.ingest(
        documents=[
            Document(
                bucket_id=int(bucket_id),
                file_name="sample-local-pdf.pdf",
                file_path=remote_pdf_url,
                file_type="pdf",
                search_data={"test": "upload_poller_integration"},
            )
        ]
    )

    # Extract process_id
    if hasattr(ingest_response, 'ingest'):
        process_id = ingest_response.ingest.process_id
    else:
        process_id = ingest_response["ingest"].get("processId")

    assert process_id is not None
    logger.info("Polling process_id=%s", process_id)

    # 3. Use the poller with the logger passed in
    final_state = upload_poller(
        client=client,
        process_id=process_id,
        poll_interval=2.0,
        timeout=300,
        logger=logger,  # Integrated logging
        print_completed=True,
    )

    logger.info("Final upload state: %s", final_state)

    assert isinstance(final_state, str)
    assert final_state in {"complete", "error", "cancelled", "inactive"}
    
    # Optional cleanup: Delete the bucket after successful test
    client.buckets.delete(bucket_id=bucket_id)