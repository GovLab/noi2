[![Build Status](https://travis-ci.org/GovLab/noi2.svg?branch=master)](https://travis-ci.org/GovLab/noi2)

# Network of Innovators

## Quick install

To get an deployment of NOI running quickly on a Linux box with Docker
installed (for example, a DigitalOcean droplet), run the following in terminal:

    curl -L https://github.com/docker/compose/releases/download/1.4.2/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
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
    ADMINS:
      - admin@example.org

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

Then, you need to pul the images.  This will take a minute the first time.
If requirements change, you need to do this again.

    docker-compose pull

You may also want to seed the database with a bunch of random users and
other data, which can be done via:

    ./manage.sh populate_db

### Running the server

To get everything running:

    docker-compose up

### OS X Notes

Please install [Docker Toolbox][]. This will ensure that you have
Docker, Docker Machine, and Docker Compose on your system.

#### Viewing the site on Mac

Since Docker Machine doesn't expose containers to `localhost` or
`127.0.0.1`, you will need to go to the IP address you get from

    docker-machine ip default

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
`translations/<locale>/LC_MESSAGES/messages.po`, then run

    ./manage.sh translate_compile

To generate the `.mo` file used in actual translation.  Successive runs of the
script won't destroy any data in the `.po` file, which is kept in version
control.

### Unit Testing

To run the unit tests, simply run:

    ./nosetests.sh

This just executes [`nosetests`][] inside the web application's Docker
container.

Tests are located in `app/tests`. Please feel free to add more!

### Changing the Dockerfile

This app uses *two* different Dockerfiles:

* `app/Dockerfile` is the "base" container for the app; it's hosted on
  [Docker Hub][] and retrieved from there. It's fairly large, takes a long
  time to build; it's also versioned and shouldn't change very often.
* `app/docker-quick/Dockerfile` sits atop the base container and is
  built on development/production infrastructure. It shouldn't take
  long to build, and its contents should regularly be moved over to
  `app/Dockerfile` and tagged as a new version on Docker Hub.

This is done to make it fast to get new deploys and Travis CI builds
up and running, while also making it easy to experiment with new
dependencies.

#### Updating app/docker-quick/Dockerfile

This Dockerfile is easy to update; just change the file or
`requirements.quick.txt` as needed and re-run `docker-compose build` to
rebuild the container.

You may want to run `docker-compose run app bash` to poke into your
newly-built container and make sure things work.

#### Updating app/Dockerfile

Updating this Dockerfile takes more work:

1. Find the current version of the base dockerfile by looking at
   the `FROM` directive of `app/docker-quick/Dockerfile`. The rest
   of these instructions assume it is `docker-base-0.1` for the sake of
   example.
2. Move lines from `app/docker-quick/Dockerfile` and 
   `requirements.quick.txt` over to `app/Dockerfile` and `requirements.txt`
   as needed.
3. Commit the changes and tag the revision with `git tag docker-base-0.2`.
4. Push the changes to GovLab/noi2 on GitHub with
   `git push git@github.com:GovLab/noi2.git docker-base-0.2`. This will
   trigger a new build of the container on Docker Hub, which you can
   monitor at Docker Hub's [Build Details][] page.
5. Once Docker Hub is finished, update the `FROM` directive of
   `app/docker-quick/Dockerfile` to point to `docker-base-0.2`.

### Editing CSS

We use [SASS][] for our styles; all files are contained in
`app/static/sass`.

We also use the [PostCSS Autoprefixer][] to post-process the compiled
CSS and ensure that it works across all browsers.

When `DEBUG` is `True` (i.e., during development), we use SASS
middleware to dynamically recompile SASS to CSS on-the-fly; however,
this middleware has a few drawbacks.

For technical reasons, the dynamically-compiled CSS is actually served
from a different directory than the precompiled CSS is served from in
production. Because of this, links to compiled SASS in templates need
to use the `COMPILED_SASS_ROOT` global, while links to static assets
(like images) in SASS need to use the `$path-to-static` variable.

For more details on how we write our SASS, see the project's
[SASS README][].

  [`nosetests`]: https://nose.readthedocs.org/en/latest/usage.html
  [Docker Toolbox]: https://www.docker.com/toolbox
  [Build Details]: https://hub.docker.com/r/thegovlab/noi2/builds/
  [SASS]: http://sass-lang.com/
  [PostCSS Autoprefixer]: https://github.com/postcss/autoprefixer
  [SASS README]: https://github.com/GovLab/noi2/blob/master/app/static/sass/README.md
  [Docker Hub]: https://hub.docker.com/r/thegovlab/noi2/
