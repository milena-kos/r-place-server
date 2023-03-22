import socket, threading, time, catbase

PORT = 30128

db = catbase.CatDB("db.json", none=0)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', PORT))

server.listen()

clients = []
responses = {}

levelcode = db["levelcode"]
cooldowns = db["cooldowns"]

if not levelcode:
    db["levelcode"] = "V1;75;75;;;;"
    db.commit()

def broadcast(message, addr):
    for k, v in responses.items():
        if k == addr: continue
        v.append(message)
        responses[k] = v

def handle(client, address):
    client.send(db["levelcode"].encode("ascii"))
    while True:
        try:
            message = client.recv(256).decode("ascii") # receive up to 256 bytes from client.
            if message == "heartbeat":
                if responses[address[0]] != []:
                    client.send(responses[address[0]][0].encode("ascii"))
                    responses[address[0]].pop(0)
                else:
                    client.send("heartbeat".encode("ascii"))
                continue
            # ensure cooldown isnt bypassed
            if time.time() - db[str(address[0])] >= 60 and len(message.split(".")) == 4:
                print(message)
                db[str(address[0])] = time.time()

                current = db["levelcode"]
                cells = current.split(";")[4].split(",")
                res = "V1;75;75;;"
                result = ""

                found = False
                for i in cells:
                    if i.split(".")[-2:] == message.split(".")[-2:]:
                        i = message
                        found = True
                        if i[0] == "N":
                            continue
                    result += i + ","

                if not found:
                    result += message + ","
                    
                if result[0] == ",": result = result[1:]

                res += result[:-1] + ";;"

                db["levelcode"] = res
                db.commit()
                client.send(message.encode("ascii"))
                broadcast(message, address[0])
            elif message:
                client.send("heartbeat".encode("ascii"))
            else:
                raise Exception # message is empty, only possible if client is down
        except Exception as e:
            print(f"Disconnected with {str(address[0])} - {e}!")
            clients.remove(client)
            responses[address[0]] = []
            client.close()
            return

def receive():
    while True:
        # accept anyone
        client, address = server.accept()
        print(f"Connected with {address}!")

        clients.append(client)
        responses[address[0]] = []

        thread = threading.Thread(target=handle, args=(client, address,))
        thread.start()

receive()
