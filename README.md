# Network of Innovators

## Development

To develop, install the pip requirements into a virtualenv.  You will need
Docker.

    virtualenv .env
    source .env/bin/activate
    pip install -r requirements.txt

If you're using `pylint` (which you should) you'll also want to install the
app's dependencies into your virtualenv.  This will allow pylint to tell you if
you're using a pip library wrong.

    pip install -r app/requirements.txt

If you have a global `pylint` installed, you should remove it as it won't be
able to track dependencies properly.

Then, you need to build the images.  This will take a minute the first time.
If requirements change, you need to do this again.

    docker-compose build

### Mac OSX OpenSSL issues

If an OpenSSL error is preventing `docker-compose build` from working on Mac
OSX, you'll need to install `docker-compose` via `curl` instead of `pip`:

    curl -L https://github.com/docker/compose/releases/download/1.3.3/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

You may need to prepend `sudo` to the commands above depending on your system's
permissions.

### Running the server

To get everything running:

    docker-compose up

### Viewing pages on Mac

Since boot2docker doesn't expose containers to `localhost` or `127.0.0.1`, you
will need to go to the IP address you get from

    boot2docker ip

The server should be running on port 5000.
