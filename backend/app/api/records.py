from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_records():
    return {"records": []}


@router.post("/")
async def create_record():
    return {"message": "Record created"}
