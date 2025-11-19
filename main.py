import uvicorn

from auth.routers import router as auth_router
from users.routers import router as users_router
from chat.routers import router as chat_router
from chat.connection_manager import manager
from fastapi import FastAPI


app = FastAPI()
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router)


@app.get("/")
async def read_root():
    await manager.start()
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
