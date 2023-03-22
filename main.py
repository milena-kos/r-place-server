import socket, threading, time, catbase

db = catbase.CatDB("db.json", none=0)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 8080))

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
                    print(responses[address[0]][0])
                    client.send(responses[address[0]][0])
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
                result = "V1;75;75;;"

                found = False
                for i in cells:
                    if i.split(".")[-2:] == message.split(".")[-2:]:
                        i = message
                        found = True
                        if i[0] == "N":
                            continue
                    result = result + i + ","

                if not found:
                    result += message + ","

                result = result[:-1] + ";;"

                db["levelcode"] = result
                db.commit()
                client.send(message.encode("ascii"))
                broadcast(message, address[0])
            else:
                client.send("heartbeat".encode("ascii"))
        except ConnectionResetError:
            print(f"Disconnected with {str(client)}!")
            clients.remove(client)
            client.close()
            break

def receive():
    while True:
        # accept anyone
        client, address = server.accept()
        print(f"Connected with {address}, {str(client)}!")

        clients.append(client)
        responses[address[0]] = []

        print("stargint a threat")
        thread = threading.Thread(target=handle, args=(client, address,))
        thread.start()

receive()
