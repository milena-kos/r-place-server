# r-place-server
An official server for r/place in Cell Machine. Uses MongoDB.

# Run
(note: i havent even done this myself yet)
1. `pip install` the requirements.
2. Get a MongoDB database running and set the following env variables:
- MONGOHOST
- MONGOPORT
- MONGOUSER
- MONGOPASSWORD
- MONGO_URL
3. Run `main.py`
4. Modify the r/place CMMM mod source code to connect to your server.
