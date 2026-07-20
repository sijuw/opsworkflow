from fastapi import APIRouter

router = APIRouter(prefix="/response-codes", tags=["Response Codes"])

RESPONSE_CODES = [
    {"code": "91", "description": "Issuer or Switch Inoperative"},
    {"code": "96", "description": "System Malfunction"},
    {"code": "05", "description": "Do Not Honor"},
    {"code": "14", "description": "Invalid Card"},
    {"code": "51", "description": "Insufficient Funds"},
]

@router.get("")
def get_response_codes():
    return RESPONSE_CODES