# This script can be used to quickly configure a Discourse instance
# to properly work with NoI SSO.
#
# To use it on a Docker-based deployment of Discourse:
#
# (1) Edit the NOI_ORIGIN and SSO_SECRET constants below.
# (2) Copy the contents of this script to your clipboard.
# (3) From the root of your Discourse checkout, run:
#
#     ./launcher enter app
#     rails c
#
# (4) Paste the contents of your clipboard.
# (5) Type "exit" to exit the Ruby shell, and "exit" again to exit
#     the Docker container.

# Set this to the origin of your NoI deployment.
NOI_ORIGIN = "https://networkofinnovators.org"

# This needs to be identical to DISCOURSE.sso_secret in your NoI config.
SSO_SECRET = "PUT_YOUR_SSO_SECRET_HERE"

# You will probably want to require login to view the Discourse site.
# This also makes sharing login state between Discourse and NoI much
# more fluid and less confusing.
SiteSetting.login_required = true

SiteSetting.enable_sso = true
SiteSetting.sso_url = "#{NOI_ORIGIN}/discourse/sso"
SiteSetting.sso_secret = SSO_SECRET
SiteSetting.sso_overrides_email = true
SiteSetting.sso_overrides_username = true
SiteSetting.sso_overrides_name = true
SiteSetting.sso_overrides_avatar = true
SiteSetting.logout_redirect = "#{NOI_ORIGIN}/logout"

# It's strongly recommended that you install the Discourse-Webhooks plugin:
#
#   https://github.com/rcfox/Discourse-Webhooks
#
# This will ensure that NoI's reflection of Discourse activity remains
# accurate.
if SiteSetting.respond_to? :webhooks_enabled
  SiteSetting.webhooks_enabled = true
  SiteSetting.webhooks_registered_events = "topic_created|post_created"
  SiteSetting.webhooks_url_format = "#{NOI_ORIGIN}/discourse/webhook/%{event_name}"
end
