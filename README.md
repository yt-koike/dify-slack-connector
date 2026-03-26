# Dify Slack Connector

This software connects Dify and Slack.

# How to use

1. For initialisation, `docker compose run init`
2. If you want to start it, `docker compose up slack_dify -d`
3. If you want to see the log, `docker compose logs -f`
4. If you want to stop it, type `docker compose down`.

# Cron

You can set up a cron job to run this software every minute.

If enable_cron_announce is set to true, cron will see the response and send a message to specified channel.
The first line of the response is the channel id, and the rest is the message.
