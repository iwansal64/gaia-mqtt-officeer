import json
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/auth")
async def auth(request: Request):
    body = dict(await request.json())
    username, password = body.get("username"), body.get("password")
    if username == "iwan" and password == "secret":
      return "ok"
    raise HTTPException(status_code=401)

@app.post("/superuser")
async def superuser(request: Request):
    raise HTTPException(status_code=401)

@app.post("/acl")
async def acl(request: Request):
    body = dict(await request.json())
    username, topic, acc = body.get("username"), body.get("topic"), body.get("acc")
    if topic.startswith(f"{username}/"):  # each user gets their own namespace
        return "ok"
    raise HTTPException(status_code=401)
