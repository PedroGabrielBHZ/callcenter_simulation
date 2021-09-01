# Call center Simulator
A basic example to deploy a Twisted Call Center server-client application as a Docker container.

# Requirements
- Python 3.x
- Docker (just get the latest, I guess)
- Docker Compose (idem)

# Dockerfile

The Dockerfile installs all necessary requirements to properly run twisted in a *nix environment.

## Server Config

### Port
Just set an environment variable called **ECHO_SERVER_PORT** and define a value.
By default, the server will run at the 5678 port. 

# Running the server on Docker
```
git clone https://github.com/PedroGabrielBHZ/callcenter_simulation.git
cd callcenter_simulation/app/server
export ECHO_SERVER_PORT=5678
docker-compose up
```
# Running the server locally

You also can run the server app locally.
Follow this steps:

```
git clone https://github.com/PedroGabrielBHZ/callcenter_simulation.git
cd callcenter_simulation/app/server
pip3 install -r requirements.txt
export ECHO_SERVER_PORT=5678
twistd --nodaemon --python callcenter_server.py
```

After the image, the container will be started. Check with:

```
docker ps
```

# Running the client locally

When the container starts, to interact with the server locally, do:
```
cd ../app/client
pip3 install -r requirements.txt
twistd --nodaemon --python callcenter_client.tac
```
