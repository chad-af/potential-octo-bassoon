from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def healthcheck():
    return "health check!"


@router.post("/token")
async def get_token():
    # In a real-world scenario, you'll need to authenticate the user and generate a token
    return {"access_token": "your-access-token", "token_type": "bearer"}
