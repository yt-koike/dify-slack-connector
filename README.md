# Dify Slack Connector
This software connects Dify and Slack.

# How to use
1. Fill in the `slack_dify_secret_template.yml` with your API keys.
You'll need [App-level tokens](https://api.slack.com/concepts/token-types#app-level) and [Bot tokens](https://api.slack.com/concepts/token-types#bot) for Slack.

2. Rename `slack_dify_secret_template.yml` to `.slack_dify_secret.yml`.
3. `docker compose up -d`
4. If you want to stop it, type `docker compose up -d`.
