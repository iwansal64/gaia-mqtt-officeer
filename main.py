from fastapi import FastAPI, Request, HTTPException
import dotenv
import psycopg

#? Server Handler
app = FastAPI()

#? PostgreSQL Handler
conn = psycopg.connect(dotenv.get_key("./.env", "DATABASE_URL"))


#? Routes
@app.post("/auth")
async def auth(request: Request):
    body = dict(await request.json())
    username, password = body.get("username"), body.get("password")

    with conn.cursor() as cur:
        #? Get the user data
        cur.execute("SELECT access_token FROM users WHERE id = %s", (username,))
        user_data = cur.fetchone()

        #? If there's user data recorded with the user id
        if user_data:
            
            #? If the password is correct
            if user_data[0] == password:
                return "ok"
                
            #? If the password is wrong
            else:
                return HTTPException(status_code=401)

        #? If there's no user data, maybe it's a device?
        cur.execute("SELECT access_token FROM devices WHERE id = %s", (username,))
        device_data = cur.fetchone()

        #? If there's device data recorded with the device id
        if device_data:
            
            #? If the password is correct
            if device_data[0] == password:
                return "ok"
                
            #? If the password is wrong
            else:
                return HTTPException(status_code=401)
        

        #? The id given by the client is not valid
        raise HTTPException(status_code=401)



@app.post("/superuser")
async def superuser(request: Request):
    raise HTTPException(status_code=401)
    
    

@app.post("/acl")
async def acl(request: Request):
    body = dict(await request.json())
    username, topic, acc = body.get("username"), body.get("topic"), body.get("acc")


    with conn.cursor() as cur:
        #? Get the connections by user id
        cur.execute("SELECT device_id FROM connections WHERE user_id = %s", (username,))
        connections_data = cur.fetchall()
        
        #? If there's connections data by user id
        if len(connections_data) > 0:
            
            #? Check for each connection data
            for row in connections_data:

                #? If there's a connection between the topic and the user
                if row[0] == topic:
                    return "ok"
        
        #? If there's no connection data by user id, maybe it's a device?
        cur.execute("SELECT user_id FROM connections WHERE device_id = %s", (username,))
        connections_data = cur.fetchall()

        #? If there's connecton data by device id
        if len(connections_data) > 0:
            
            #? If the username is the same as the topic (only sending data to their own topic)
            if username == topic:
                return "ok"
    
    raise HTTPException(status_code=401)
