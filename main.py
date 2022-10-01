import pymongo, os, socket, threading, time, cell_machine_levels

mongoclient = pymongo.MongoClient(os.environ["MONGO_URL"])
db = mongoclient["rplace"]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', os.environ["PORT"]))

server.listen()

clients = []

levelcode = db["levelcode"]
cooldowns = db["cooldowns"]

if not levelcode.find_one(): # if we have no level code stored
	levelcode.insert_one({"code": "V1;75;75;;;;"})

def to_v3(v1_code):
	convert = cell_machine_levels.level.open(v1_code)
	return convert.save("V3")

def broadcast(message):
	for client in clients: 
		client.send(message)

def handle(client, address):
	client.send(to_v3(levelcode.find_one()["code"]).encode("utf-8"))
	while True:
		try:
			message = client.recv(256).decode("utf-8") # receive up to 256 bytes from client.
			# ensure cooldown isnt bypassed
			if time.time() - cooldowns.find_one({"ip": address})["time"] >= 60:
				cooldowns.replace_one({"ip": address}, {"ip": address, "time": time.time()})
				
				current = levelcode.find_one()["code"]
				cells = current.split(";")[4].split(",")
				result = "V1;75;75;;"
				
				for i in cells:
					# N means "remove cell"
					if i[0] != "N":
						if i.split(".")[-2:] == message.split(".")[-2:]:
							i = message
						result = result + message + ","
				
				result = result[:-1] + ";;"
				
				levelcode.replace_one({"code": current}, result)
				broadcast(message)
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
		
		if not cooldowns.find_one({"ip": address}):
			cooldowns.insert_one({"ip": address, "time": 0})

		clients.append(client)

		thread = threading.Thread(target=handle, args=(client, address,))
		thread.start()

receive()