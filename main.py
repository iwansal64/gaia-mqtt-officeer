from fastapi import FastAPI, Request, HTTPException
from datetime import datetime
import dotenv
import psycopg
import config
import atexit

#? Convinient Constants
READ = 4
PASS = 1
WRITE = 2

#? Server Handler
app = FastAPI()

#? PostgreSQL Handler
postgres_url = dotenv.get_key("./.env", "DATABASE_URL")
if postgres_url == None:
    print("DATABASE_URL doesn't exists!")
    exit(1)
    
conn = psycopg.connect(postgres_url)


#? Setup Logger
log_file = open(f"logs/{datetime.now().strftime('%d-%m-%Y')}.log", "a+")
def print_log(msg: str, end: str = "\n"):
    current_time = datetime.now().strftime("%H:%M:%S")
    log_file.write(f"[{current_time}]"+msg+end)


#? Setup Exit Handler
def exit_handler():
    log_file.close()

atexit.register(exit_handler)


#? Routes
@app.post("/auth")
async def auth(request: Request):
    global postgres_url
    if postgres_url == None:
        print("DATABASE_URL doesn't exists!")
        raise HTTPException(status_code=500)

    conn = psycopg.connect(postgres_url)
    
    body = dict(await request.json())
    username, password = str(body.get("username")), str(body.get("password"))
    
    print_log(f"[Auth] Attempt to access {username}");
    with conn.cursor() as cur:
        #? Get the user data
        cur.execute("SELECT access_token FROM users WHERE id = %s", (username,))
        user_data = cur.fetchone()

        #? --------- USER ---------
        #? If there's user data recorded with the user id
        if user_data:
            
            #? If the password is correct
            if user_data[0] == password:
                print_log(f"[Auth] User {username} GRANTED!");
                return "ok"
                
            #? If the password is wrong
            else:
                print_log(f"[Auth] User {username} UNAUTHORIZED!");
                raise HTTPException(status_code=401)

        #? If there's no user data, maybe it's a device?
        cur.execute("SELECT access_token FROM devices WHERE id = %s", (username,))
        device_data = cur.fetchone()

        #? --------- DEVICE ---------
        #? If there's device data recorded with the device id
        if device_data:
            
            #? If the password is correct
            if device_data[0] == password:
                print_log(f"[Auth] Device {username} GRANTED!");
                return "ok"
                
            #? If the password is wrong
            else:
                print_log(f"[Auth] Device {username} UNAUTHORIZED!");
                return HTTPException(status_code=401)
        

        #? The id given by the client is not valid
        raise HTTPException(status_code=401)



@app.post("/superuser")
async def superuser(request: Request):
    raise HTTPException(status_code=401)
    
    

@app.post("/acl")
async def acl(request: Request):
    global postgres_url
    if postgres_url == None:
        print("DATABASE_URL doesn't exists!")
        raise HTTPException(status_code=500)
    
    conn = psycopg.connect(postgres_url)
    
    body = dict(await request.json())
    username, topic, acc = str(body.get("username")), str(body.get("topic")), int(str(body.get("acc"))) # 1 = read, 2 = write, 3 = read-write

    if "/" not in topic:
        raise HTTPException(status_code=401)

    with conn.cursor() as cur:
        #? Get the connections by user id
        cur.execute("SELECT device_id FROM connections WHERE user_id = %s AND user_accepted = true AND device_accepted = true", (username,))
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
        cur.execute("SELECT user_id FROM connections WHERE device_id = %s", (username,))
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
