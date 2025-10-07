from fastapi import FastAPI, Request, HTTPException
import dotenv
import psycopg
import config

READ = 4
PASS = 1
WRITE = 2

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

        #? --------- USER ---------
        #? If there's user data recorded with the user id
        if user_data:
            
            #? If the password is correct
            if user_data[0] == password:
                return "ok"
                
            #? If the password is wrong
            else:
                raise HTTPException(status_code=401)

        #? If there's no user data, maybe it's a device?
        cur.execute("SELECT access_token FROM devices WHERE id = %s", (username,))
        device_data = cur.fetchone()

        #? --------- DEVICE ---------
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
    username, topic, acc = body.get("username"), body.get("topic"), body.get("acc") # 1 = read, 2 = write, 3 = read-write

    if "/" not in topic:
        raise HTTPException(status_code=401)

    with conn.cursor() as cur:
        #? Get the connections by user id
        cur.execute("SELECT device_id FROM connections WHERE user_id = %s", (username,))
        connections_data = cur.fetchall()
        
        
        #? --------- USER ---------
        #? If there's connections data by user id
        if len(connections_data) > 0:
            
            #? If the username is the same as the topic (only sending data to their own topic)
            splitted_topic = str(topic).split("/", 2)
            main_topic, subtopic = splitted_topic[0], splitted_topic[1]

            #? Check for each connection data
            for row in connections_data:
                device_id = row[0]
                
                #? If the main topic is the device id in the connection
                if main_topic == device_id:
                    #? If the access mode is WRITE
                    if acc == WRITE and subtopic in config.user_allowed_subtopics:
                        return "ok"

                    #? If the access mode is READ or PASS
                    if (acc == READ or acc == PASS) and subtopic in config.device_allowed_subtopics:
                        return "ok"
                    
                    
        
        #? If there's no connection data by user id, maybe it's a device?
        cur.execute("SELECT id FROM connections WHERE device_id = %s", (username,))
        connections_data = cur.fetchall()

        
        #? --------- DEVICE ---------
        #? If there's connecton data by device id
        if len(connections_data) > 0:
            
            #? If the username is the same as the topic (only sending data to their own topic)
            splitted_topic = str(topic).split("/", 2)
            main_topic, subtopic = splitted_topic[0], splitted_topic[1]
            
            #? If the main topic is the username itself
            if main_topic == username:
                
                #? If the access mode is WRITE
                if acc == WRITE and subtopic in config.device_allowed_subtopics:
                    return "ok"

                #? If the access mode is READ
                if (acc == READ or acc == PASS) and subtopic in config.user_allowed_subtopics:
                    return "ok"
    
    raise HTTPException(status_code=401)
