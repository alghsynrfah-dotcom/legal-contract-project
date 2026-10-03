
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Query, BackgroundTasks
from pydantic import BaseModel

from shared.db import SessionLocal
from shared.models import Contract
from shared.storage import save_file, delete_contract_files
from shared.errors import AppError, contract_not_found


router = APIRouter(prefix="/api/contracts", tags=["contracts"])


# --------------------------------------------------
# Allowed file types
# --------------------------------------------------

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# --------------------------------------------------
# Response schemas
# --------------------------------------------------

class ContractResponse(BaseModel):
    contract_id: str
    name: str
    file_type: str
    uploaded_at: str
    status: str
    ingestion_status: str


class ContractDetailsResponse(ContractResponse):
    start_date: str | None = None
    end_date: str | None = None


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _serialize_contract(contract: Contract) -> dict:
    return {
        "contract_id": contract.contract_id,
        "name": contract.name,
        "file_type": contract.file_type,
        "uploaded_at": (
            contract.uploaded_at.isoformat()
            if contract.uploaded_at
            else None
        ),
        "status": contract.status,
        "ingestion_status": contract.ingestion_status,
    }


def _get_contract(contract_id: str) -> Contract:
    with SessionLocal() as db:
        contract = db.get(Contract, contract_id)

        if not contract:
            raise contract_not_found(contract_id)

        return contract


# --------------------------------------------------
# 1. Upload Contract
# --------------------------------------------------

@router.post("/upload")
def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a contract.

    Flow:
        File
          ↓
        Save in Storage
          ↓
        Create contract_id
          ↓
        Save contract metadata in DB
          ↓
        Start ingestion
    """

    if not file.filename:
        raise AppError(
            "INVALID_FILE",
            "A file name is required",
            422,
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise AppError(
            "UNSUPPORTED_FILE_TYPE",
            "Only PDF, DOCX and TXT files are supported",
            422,
        )

    try:
        data = file.file.read()

        if not data:
            raise AppError(
                "EMPTY_FILE",
                "The uploaded file is empty",
                422,
            )

        # Create the database record first.
        # SQLAlchemy generates the contract UUID.
        with SessionLocal() as db:
            contract = Contract(
                name=Path(file.filename).name,
                file_type=extension.lstrip("."),
                file_path="",
                status="Active",
                ingestion_status="processing",
            )

            db.add(contract)
            db.commit()
            db.refresh(contract)

            contract_id = contract.contract_id

        # Save the actual file using the shared storage service.
        storage_key = save_file(
            contract_id,
            file.filename,
            data,
        )

        # Save the storage path in DB.
        with SessionLocal() as db:
            contract = db.get(Contract, contract_id)

            if not contract:
                delete_contract_files(contract_id)
                raise contract_not_found(contract_id)

            contract.file_path = storage_key
            db.commit()

        # Start text extraction → chunking → embedding → RAG.
        #
        # This function will be implemented in:
        # app/ingestion.py
        from .ingestion import ingest_contract

        background_tasks.add_task(
            ingest_contract,
            contract_id,
        )

        return {
            "contract_id": contract_id,
            "name": Path(file.filename).name,
            "file_type": extension.lstrip("."),
            "ingestion_status": "processing",
            "message": "Contract uploaded successfully",
        }

    except AppError:
        raise

    except Exception as e:
        raise AppError(
            "UPLOAD_FAILED",
            f"Could not upload contract: {e}",
            500,
        )


# --------------------------------------------------
# 2. List Contracts
# --------------------------------------------------

@router.get("")
def list_contracts(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
):
    """
    Return all saved contracts.

    Optional:
        ?search=contract-name
    """

    with SessionLocal() as db:
        query = db.query(Contract)

        if search:
            query = query.filter(
                Contract.name.ilike(f"%{search.strip()}%")
            )

        contracts = query.order_by(
            Contract.uploaded_at.desc()
        ).all()

        return {
            "contracts": [
                _serialize_contract(contract)
                for contract in contracts
            ]
        }


# --------------------------------------------------
# 3. Contract Details
# --------------------------------------------------

@router.get("/{contract_id}")
def get_contract_details(contract_id: str):
    """
    Return complete information about one contract.
    """

    with SessionLocal() as db:
        contract = db.get(Contract, contract_id)

        if not contract:
            raise contract_not_found(contract_id)

        return {
            "contract_id": contract.contract_id,
            "name": contract.name,
            "file_type": contract.file_type,
            "uploaded_at": (
                contract.uploaded_at.isoformat()
                if contract.uploaded_at
                else None
            ),
            "status": contract.status,
            "ingestion_status": contract.ingestion_status,
            "start_date": (
                contract.start_date.isoformat()
                if contract.start_date
                else None
            ),
            "end_date": (
                contract.end_date.isoformat()
                if contract.end_date
                else None
            ),
        }


# --------------------------------------------------
# 4. Delete Contract
# --------------------------------------------------

@router.delete("/{contract_id}")
def delete_contract(contract_id: str):
    """
    Delete a contract and its stored files.

    Contract chunks are deleted automatically
    because ContractChunk uses ON DELETE CASCADE.
    """

    with SessionLocal() as db:
        contract = db.get(Contract, contract_id)

        if not contract:
            raise contract_not_found(contract_id)

        db.delete(contract)
        db.commit()

    # Delete physical files after DB deletion.
    delete_contract_files(contract_id)

    return {
        "contract_id": contract_id,
        "message": "Contract deleted successfully",
    }
