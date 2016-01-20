# How to set up an NoI instance

1. Create a DigitalOcean droplet

  * You can use the $5/month droplet
  * Give it an informative name (for example "noi-usg" for usg.networkofinnovators.org)
  * Locate it in a data center as close as possible to the user base
  * Use the "Docker" image.  You can find this by selecting "Applications" under **Select Image**, then "Docker x.x.x on x.x" (As of when this was written, that was "Docker 1.8.2 on 14.04")
  * Add all available SSH Keys.  If yours is not on the list, make sure to add it and then select it.

2. Attach the IP of the DigitalOcean droplet to the domain

  * The IP address will be visible in the DigitalOcean control panel once the droplet is ready, which takes about a minute.
  * Use an A record to attach the relevant (sub)domain to the droplet's IP address.

3. Log into the droplet and follow the [Quick Install](https://github.com/govlab/noi2#quick-install) instructions in the README

  * If SSH keys are set up correctly, you should be able to log in with `ssh root@the.domain.com`.

4. Move to the `stable` version

  * `git checkout stable`

4. Configure the site

  * Open up `app/config/local_config.yml` in your text editor of choice
    and edit it to taste, using [`local_config.sample.yml`](https://github.com/GovLab/noi2/blob/master/app/config/local_config.sample.yml) as a guide.
    Make sure that you've at least set `DEBUG` to `False`, specified an
    unguessable `SECRET_KEY`, and set `NOI_DEPLOY`. You'll probably also
    want to configure mail and S3.
  * Some credentials can be obtained from prior installations.
  * Other customizations (about text, questionnaire ordering, language, etc.) should be made in [deployments.yaml](https://github.com/GovLab/noi2/blob/master/app/data/deployments.yaml).  You'll need to branch these changes off of `stable`, and make sure to re-tag the new commit as `stable`.

5. Set up https

  * Make sure you have a cert that will work for your subdomain, or are using a wildcard.
  * Create a directory `.keys` if it does not yet exist, and add the files `dhparams.pem`, `noi-ssl-certificate`, and `noi-ssl-key` with relevant keys and certs. See [conf/ssl/ssl.conf](https://github.com/GovLab/noi2/blob/master/conf/ssl/ssl.conf) for reference.

6. Run it!

  * `./deploy.sh` should get everything rolling
  * If you initially get a 502, the migrations may have gotten stuck.  Go back to the terminal and run `docker-compose stop`, then `./deploy.sh` again.
  * To view logs, run `docker-compose logs`.
  * Run `./manage.sh test_email_error_reporting` to ensure error reports
    are emailed properly.
