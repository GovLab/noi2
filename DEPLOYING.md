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
  * Add the following lines, substituting those in carrots:

  ```
MAIL_USERNAME: <Gmail or Gmail-hosted user to send mail from>
MAIL_PASSWORD: <One-off password for that account>
NOI_DEPLOY: <Hostname of this deployment>
S3_ACCESS_KEY_ID: <S3 key for image uploads>
S3_SECRET_ACCESS_KEY: <S3 secret for that key>
DEBUG: False
GA_TRACKING_CODE: <Google Analytics tracking code>
SECRET_KEY: <Encryption key for this deployment, `cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1` in shell will work>
ADMINS:
  - admin@example.org
  - <Other emails to send error reports to>
  ```

  * Some of these credentials can be obtained from prior installations.
  * Other customizations (about text, questionnaire ordering, language, etc.) should be made in [deployments.yaml](https://github.com/GovLab/noi2/blob/master/app/data/deployments.yaml).  You'll need to branch these changes off of `stable`, and make sure to re-tag the new commit as `stable`.

5. Set up https

  * Make sure you have a cert that will work for your subdomain, or are using a wildcard
  * Uncomment all the lines in [conf/ssl/ssl.conf](https://github.com/GovLab/noi2/blob/master/conf/ssl/ssl.conf).
  * Add additional `ssl_ciphers`, `ssl_prefer_server_ciphers`, and `ssl_dhparam` from another deployment if they're available.
  * Create a directory `.keys` if it does not yet exist, and add the files `dhparams.pem`, `noi-ssl-certificate`, and `noi-ssl-key` with relevant keys and certs.

6. Run it!

  * `./deploy.sh` should get everything rolling
  * If you initially get a 502, the migrations may have gotten stuck.  Go back to the terminal and run `docker-compose stop`, then `./deploy.sh` again.
  * To view logs, run `docker-compose logs`.
  * Run `./manage.sh test_email_error_reporting` to ensure error reports
    are emailed properly.
