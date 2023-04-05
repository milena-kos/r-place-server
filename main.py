import socket, threading, time, json
PORT = 8802

with open("db.json", "r") as f:
	db = json.load(f)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', PORT))

server.listen()

clients = []
ips = []
responses = {}

cellKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&+-.=?^{}"

def EncodeInt(num):
    if num < 74:
        return cellKey[num]

    output = ""
    while num:
        output = cellKey[num % 74] + output
        num = num // 74
    return output

def convert(v1code):
    parts = v1code.split(";")
    output = "V3;"

    x, y = int(parts[1]), int(parts[2])
    cells = parts[4].split(",")
    output += EncodeInt(x) + ";"
    output += EncodeInt(y) + ";"

    dataIndex = 0

    cellData = [[72] * (x * y)][0]

    for i in cells:
        if not i: continue
        type, rot, x_, y_ = i.split(".")
        type, rot, x_, y_ = int(type), int(rot), int(x_), int(y_)
        cellData[x_ + (y_ * x)] += (2 * type) + (18 * rot) - 72

    maxMatchOffset = 0

    cellDataLength = len(cellData)

    while dataIndex < cellDataLength:
        maxMatchLength = 0
        for matchOffset in range(1, dataIndex):
            matchLength = 0
            try:
                while cellData[dataIndex +
                           matchLength] == cellData[dataIndex + matchLength -
                                                    matchOffset]:
                    matchLength += 1
                    if matchLength > maxMatchLength:
                        maxMatchLength = matchLength
                        maxMatchOffset = matchOffset - 1
            except Exception:
                pass
        if maxMatchLength > 3:
            tempMaxMatchOffset = EncodeInt(maxMatchOffset)
            tempMaxMatchLength = EncodeInt(maxMatchLength)
            if len(tempMaxMatchLength) == 1:
                if len(tempMaxMatchOffset) == 1:
                    output += ")" + tempMaxMatchOffset + tempMaxMatchLength
                    dataIndex += maxMatchLength - 1
                else:
                    if maxMatchLength > 3 + len(tempMaxMatchOffset):
                        output += "(" + tempMaxMatchOffset + ")" + tempMaxMatchLength
                        dataIndex += maxMatchLength - 1
                    else:
                        output += cellKey[cellData[dataIndex]]
            else:
                output += "(" + tempMaxMatchOffset + "(" + tempMaxMatchLength + ")"
                dataIndex += maxMatchLength - 1
        else:
            output += cellKey[cellData[dataIndex]]

        dataIndex += 1

    return output

def save():
    global db
    with open("db.json", "w") as f:
        json.dump(db, f)

def broadcast(message, addr):
    for k, v in responses.items():
        if k == addr: continue
        v.append(message)
        responses[k] = v

def handle(client, address):
    code = db["levelcode"]
    client.send(convert(code).encode("ascii"))
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
            shad = str(address[0])
            try:
                db[shad]
            except Exception:
                db[shad] = 0
                save()
            if time.time() - db[shad] >= 60 and len(message.split(".")) == 4:
                e = message.split(".")
                rang = [str(z) for z in range(0, 75)]
                if e[0] not in "012345678N" or e[1] not in "0123" or e[2] not in rang or e[3] not in rang:
                    client.send("heartbeat".encode("ascii"))
                    continue
                print(message)
                db[shad] = time.time()

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

                if not found and e[0] != "N":
                    result += message + ","
                    
                if result[0] == ",": result = result[1:]

                res += result[:-1] + ";;"

                db["levelcode"] = res
                save()
                client.send(message.encode("ascii"))
                broadcast(message, address[0])
            elif message:
                client.send("heartbeat".encode("ascii"))
            else:
                raise Exception # message is empty, only possible if client is down
        except Exception as e:
            print(f"Disconnected with {str(address[0])} - {e}!")
            clients.remove(client)
            ips.remove(address[0])
            responses[address[0]] = []
            client.close()
            return

def receive():
    while True:
        # accept anyone
        client, address = server.accept()
        if adderss[0] in ips:
            client.close()
            continue

        print(f"Connected with {address}!")

        clients.append(client)
        ips.append(address[0])
        responses[address[0]] = []

        thread = threading.Thread(target=handle, args=(client, address,))
        thread.start()

receive()
