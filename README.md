# Network of Innovators

## Quick install

To get an deployment of NOI running quickly on a Linux box with Docker
installed (for example, a DigitalOcean droplet), run the following in terminal:

    curl -L https://github.com/docker/compose/releases/download/1.3.3/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    git clone https://github.com/GovLab/noi2.git
    cd noi2

In order to enable full site functionality, you will need to specify the
following in `noi/app/config/local_config.yml`:

    MAIL_USERNAME:
    MAIL_PASSWORD:
    NOI_DEPLOY:
    S3_ACCESS_KEY_ID:
    S3_SECRET_ACCESS_KEY:
    DEBUG: False
    SERVER_NAME:
    GA_TRACKING_CODE:
    SECRET_KEY:

If you want SSL to work, you'll need to uncomment the lines in
`/conf/ssl/ssl.conf`, and add the secret key and certificate of the same name
to the `.keys` directory.

Then, get the database ready:

    ./manage.sh db upgrade

To run the site in deploy mode:

    ./deploy.sh

## Development

To develop, install the pip requirements into a virtualenv.  You will need Docker.

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

### Viewing the site on Mac

Since boot2docker doesn't expose containers to `localhost` or `127.0.0.1`, you
will need to go to the IP address you get from

    boot2docker ip

The server should be running on port 80.

### Database migrations

Whenever you make changes to `model.py`, you will need to generate a migration
for the database.  Alembic can generate one automatically, which you will most
likely need to tweak:

    ./manage.sh db migrate

If the generation is successful, you should receive a message like:

    Generating /migrations/versions/<migration hash>_.py ... done

Then, you should edit the migration at `migrations/versions/<migration
hash>.py`, at the very least adding a human-readable description of the purpose
of the migration.

You'll need to manually restart the server using `docker-compose up` or
`./deploy.sh`.  The migration will run automatically upon restart.

Don't forget to commit the migration in git with your new code!

### Dealing with translations

Running this will generate all necessary translation files for locales that are
in `deployments.yaml`.

    ./manage.sh translate

You'll need to populate the resulting `.po` file for each locale in
`translations/<locale>/LC_MESSAGES/messages.po`, then run the same script again

    ./manage.sh translate

To generate the `.mo` file used in actual translation.  Successive runs of the
script won't destroy any data in the `.po` file, which is kept in version
control.
