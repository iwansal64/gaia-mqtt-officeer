from fastapi import FastAPI, Form

def main():
    #? Create the FastAPI instance
    app = FastAPI()


    #? When there's someone wanted to authenticate to the MQTT
    @app.post("/auth")
    async def auth(username: str = Form(...), password: str = Form(...)):
        # TODO: lookup in PostgreSQL
        if username == "user1" and password == "secret":
            return {"allow": True}
        return {"allow": False}


    #? When there's superuser request
    @app.post("/superuser")
    async def superuser(username: str = Form(...)):
        if username == "admin":
            return {"allow": True}
        return {"allow": False}

    #? When there's someone who want to subscribe to a particular topic
    @app.post("/acl")
    async def acl(username: str = Form(...), topic: str = Form(...), acc: int = Form(...)):
        # acc = 1 (read), 2 (write), 3 (both)
        if username == "user1" and topic.startswith("sensors/user1/"):
            return {"allow": True}
        return {"allow": False}


if __name__ == "__main__":
    main()
