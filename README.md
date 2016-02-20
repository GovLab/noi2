[![Build Status](https://travis-ci.org/GovLab/noi2.svg?branch=master)](https://travis-ci.org/GovLab/noi2)

# Network of Innovators

[Network of Innovators][] (NoI) is a skill-sharing network for government &
civic innovators worldwide.

Contributions to the project are welcome! Please see [`CONTRIBUTING.md`][]
for more details.

## Prerequisites

### Git Large File Storage

This project's git repository uses [Git Large File Storage][git-lfs].
Please install it before cloning. If you're on Linux, this can be
done conveniently via [packagecloud][]. (If you've already cloned the
repository, you can obtain the large files after installing Git LFS by
running `git lfs pull`.)

### Docker

This project uses a tool called Docker to set up its environment and
dependencies. The advantage of using it is that you don't have to
install a ton of dependencies--like nginx, postgres, nodejs, and a bunch of
Python modules--on your own system. The disadvantage, however, is that you
may need to acquaint yourself with Docker.

For a basic overview, see [What is Docker?][] on the Docker website.

#### Linux

First, you'll want to install [Docker Engine][] if you haven't already.

Then install Docker Compose:

    curl -L https://github.com/docker/compose/releases/download/1.5.2/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

#### Other Platforms

Please install [Docker Toolbox][]. This will ensure that you have
Docker, Docker Machine, and Docker Compose on your system.

Finally, make sure all future work with this project is done via the
**Docker Quickstart Terminal**, *not* your standard terminal or
command prompt. Using this special terminal is critical because it
sets up some environment variables and services that are required for
Docker to work on your platform.

Note that on your operating system, the hard work is all being done
behind-the-scenes by a Linux-based virtual machine. The software used
to communicate between your OS and the VM is called [Docker Machine][].
This indirection can sometimes cause confusion and difficulties, but
this README will try to address potential issues when they may arise.

**Note to Windows Users:** Due to
[various Windows issues](https://github.com/GovLab/noi2/pull/255), it's
still probably easiest to develop NoI by setting up a Linux virtual
machine using a tool like [VirtualBox][], rather than using Docker Toolbox.
However, you're welcome to give it a shot!

### Python

Some Python scripts, like `manage.py`, work as simple convenience wrappers
around Docker to make it easier for you to develop. You probably already
have Python on your system, but if running `python` from the command-line
doesn't work, you should install it.

(If you're very familiar with Python development, note that this
project doesn't use a `virtualenv`, since the "real" work is done in
a Docker container where all the dependencies are already installed.)

## Installation

Once you've set up the prerequisites mentioned above, run:

    git clone https://github.com/GovLab/noi2.git
    cd noi2
    cp app/config/local_config.sample.yml app/config/local_config.yml

Now read `app/config/local_config.yml` and optionally edit it to taste.

## Development

Build necessary images with:

    docker-compose build

Then, get the database ready:

    python manage.py db upgrade

You may also want to seed the database with a bunch of random users and
other data, which can be done via:

    python manage.py populate_db

### Running the server

To get everything running:

    docker-compose up

If you're on Linux, your development instance of NoI will be running
at http://localhost.

Otherwise, if you're on a system using Docker Toolbox, your development
server will actually be running on your Docker Machine VM, *not* on
localhost. So to visit your development instance of NoI, you will need to
go to the IP address you get from running the following command:

    docker-machine ip default

Just visit that IP in your web browser to see your development instance
of NoI.

### Optional maildump integration

You may want to enable optional [maildump][] integration to be able
to easily test email during development. To do this, run:

```terminal
$ ln -s development.yml docker-compose.override.yml
```

When you run `docker-compose up`, you'll be able to visit port 1080
on your Docker host to see any emails that NoI sends.

### Production deployment

For information on deploying to production, including setting up SSL
and more, see [`DEPLOYING.md`][].

### Database migrations

Whenever you make changes to `model.py`, you will need to generate a migration
for the database.  Alembic can generate one automatically, which you will most
likely need to tweak:

    python manage.py db migrate

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

    python manage.py translate

You'll need to populate the resulting `.po` file for each locale in
`translations/<locale>/LC_MESSAGES/messages.po`, then run

    python manage.py translate_compile

To generate the `.mo` file used in actual translation.  Successive runs of the
script won't destroy any data in the `.po` file, which is kept in version
control.

### Unit Testing

Tests are located in `app/tests`, and [doctests][] in Python modules are
automatically found and tested too. Please feel free to add more!

To run the unit tests, run:

    python manage.py test

To run an individual test, e.g. `app/tests/test_models.py`, run:

    python manage.py test app/tests/test_models.py

If you want to do anything more advanced with test-running, consider
using:

    docker-compose run app py.test

This just executes [`py.test`][] inside the web application's Docker
container.

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

  [What is Docker?]: https://www.docker.com/what-docker
  [Docker Engine]: https://docs.docker.com/engine/installation/
  [`CONTRIBUTING.md`]: https://github.com/GovLab/noi2/blob/master/CONTRIBUTING.md
  [Network of Innovators]: https://networkofinnovators.org/
  [git-lfs]: https://git-lfs.github.com/
  [packagecloud]: https://packagecloud.io/github/git-lfs/install
  [`py.test`]: http://pytest.org/latest/usage.html
  [Docker Toolbox]: https://www.docker.com/toolbox
  [Build Details]: https://hub.docker.com/r/thegovlab/noi2/builds/
  [SASS]: http://sass-lang.com/
  [PostCSS Autoprefixer]: https://github.com/postcss/autoprefixer
  [SASS README]: https://github.com/GovLab/noi2/blob/master/app/static/sass/README.md
  [Docker Hub]: https://hub.docker.com/r/thegovlab/noi2/
  [`DEPLOYING.md`]: https://github.com/GovLab/noi2/blob/master/DEPLOYING.md
  [VirtualBox]: https://www.virtualbox.org/
  [maildump]: https://github.com/ThiefMaster/maildump
  [doctests]: https://docs.python.org/2/library/doctest.html
