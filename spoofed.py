import socket, threading, time, cell_machine_levels

db = {"levelcode": {"code": "V1;75;75;;0.0.0.0,1.1.1.1;;"}, "cooldowns": {}}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 8080))

server.listen()

clients = []

levelcode = db["levelcode"]

def to_v3(v1_code):
	#convert = cell_machine_levels.level.open(v1_code)
	#return convert.save("V3")
    return v1_code

def broadcast(message):
	for client in clients: 
		client.send(message)

def handle(client, address):
	print("sending code...")
	client.send(to_v3(levelcode["code"]).encode("utf-8"))
	while True:
		try:
			message = client.recv(256) # receive up to 256 bytes from client.
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
		print(f"Connected with {str(client)}!")

		clients.append(client)

		thread = threading.Thread(target=handle, args=(client, address,))
		thread.start()

receive()