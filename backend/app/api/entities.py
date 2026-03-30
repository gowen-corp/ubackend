from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_entities():
    return {"entities": []}


@router.post("/")
async def create_entity():
    return {"message": "Entity created"}
