import io
import os
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage

from api.core.db import SessionLocal
from api.core.logging_config import get_logger
from api.core.sql_models import FileState, VoiceFile, current_time
from api.services.llm_processor import llm_pipeline

PROJECT_ID = os.getenv("PROJECT_ID", "")
ENV = os.getenv("ENV", "")


def _storage_client():
    if ENV == "local":
        return storage.Client(
            credentials=AnonymousCredentials(),
            project="local-dev",
            client_options={
                "api_endpoint": os.getenv("STORAGE_EMULATOR_HOST", "")
            },
        )
    return storage.Client(project=PROJECT_ID)


def _result_blob_name(source_blob_name: str) -> str:
    """Place result.xlsx beside the uploaded source object."""
    source_path = Path(source_blob_name)
    folder = source_path.parent.as_posix()
    stem = source_path.stem or "audio"
    filename = f"{stem}_result.xlsx"
    return f"{folder}/{filename}" if folder != "." else filename


def _write_excel(bucket, blob_name: str, results: list[dict]) -> None:
    """Upload one workbook containing one row per successfully analyzed audio file."""
    frame = pd.DataFrame(results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="results")
    output.seek(0)
    bucket.blob(blob_name).upload_from_file(
        output,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


def _analysis_row(source_file: str, analysis) -> dict:
    if hasattr(analysis, "model_dump"):
        values = analysis.model_dump(mode="json")
    else:
        raise TypeError("llm_pipeline must return a Pydantic model or None")
    return {"source_file": source_file, **values}


def process_file(transaction_id: str, bucket_name: str, blob_name: str):
    db = SessionLocal()
    file = None
    logger = get_logger(__name__, transaction_id)
    try:
        file = (
            db.query(VoiceFile)
            .filter(VoiceFile.transaction_id == transaction_id)
            .first()
        )
        if file is None:
            raise ValueError(f"No database record for transaction {transaction_id}")

        file.status = FileState.processing  # pyright: ignore[reportAttributeAccessIssue]
        db.commit()

        client = _storage_client()
        bucket = client.bucket(bucket_name)
        source_blob = bucket.blob(blob_name)

        results: list[dict] = []
        with TemporaryDirectory() as temporary_directory:
            temporary_directory = Path(temporary_directory)
            local_source = temporary_directory / Path(blob_name).name
            source_blob.download_to_filename(local_source)

            if zipfile.is_zipfile(local_source):
                extraction_directory = temporary_directory / "extracted"
                extraction_directory.mkdir()
                with zipfile.ZipFile(local_source) as archive:
                    archive.extractall(extraction_directory)

                audio_files = sorted(
                    path
                    for path in extraction_directory.rglob("*")
                    if path.is_file() and path.suffix.lower() == ".wav"
                )
                for audio_file in audio_files:
                    analysis = llm_pipeline(audio_file)
                    if analysis is not None:
                        results.append(
                            _analysis_row(
                                str(audio_file.relative_to(extraction_directory)),
                                analysis,
                            )
                        )
            else:
                if local_source.suffix.lower() != ".wav":
                    raise ValueError("Uploaded file is neither a ZIP archive nor a WAV file")
                analysis = llm_pipeline(local_source)
                if analysis is not None:
                    results.append(_analysis_row(local_source.name, analysis))

        if not results:
            raise ValueError("No audio file returned an analysis result")

        output_blob_name = _result_blob_name(blob_name)
        _write_excel(bucket, output_blob_name, results)

        file.processed_path = f"gs://{bucket_name}/{output_blob_name}"  # pyright: ignore[reportAttributeAccessIssue]
        file.processed_at = current_time()  # pyright: ignore[reportAttributeAccessIssue]
        file.status = FileState.completed  # pyright: ignore[reportAttributeAccessIssue]
        db.commit()
        logger.info("Processing completed: %s", output_blob_name)
    except Exception:
        db.rollback()
        logger.exception("Audio processing failed")
        if file is not None:
            file.status = FileState.failed  # pyright: ignore[reportAttributeAccessIssue]
            db.commit()
    finally:
        db.close()
