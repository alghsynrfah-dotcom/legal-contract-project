class AppError(Exception):
    """Unified application error -> returned as JSON by the API."""
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status

def contract_not_found(cid): return AppError("CONTRACT_NOT_FOUND", f"Contract '{cid}' not found", 404)
