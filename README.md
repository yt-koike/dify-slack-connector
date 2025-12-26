# Dify Slack Connector

This software connects Dify and Slack.

# How to use

1. Fill in the `slack_dify_secret_template.yml` with your API keys.
   You'll need [App-level tokens](https://api.slack.com/concepts/token-types#app-level) and [Bot tokens](https://api.slack.com/concepts/token-types#bot) for Slack.

2. Rename `slack_dify_secret_template.yml` to `.slack_dify_secret.yml`.
3. `docker compose up -d`
4. If you want to stop it, type `docker compose down`.

# Cron

You can set up a cron job to run this software every minute.

If enable_cron_announce is set to true, cron will see the response and send a message to specified channel.
The first line of the response is the channel id, and the rest is the message.
