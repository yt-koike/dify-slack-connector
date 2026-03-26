#!/bin/bash

OUTPUT_FILE="/secrets/secret.yml"

echo "=== Slack 設定 ==="
read -p "slack_bot_token (xoxb-...): " slack_bot_token
read -p "slack_app_token (xapp-...): " slack_app_token

echo ""
echo "=== Dify 設定 ==="
read -p "dify_scheme (http/https) [http]: " dify_scheme
dify_scheme=${dify_scheme:-http}

read -p "dify_endpoint [127.0.0.1]: " dify_endpoint
dify_endpoint=${dify_endpoint:-127.0.0.1}

read -p "dify_api_key (app-...): " dify_api_key

echo ""
echo "=== Cron 設定 ==="
read -p "enable_cron (true/false) [true]: " enable_cron
enable_cron=${enable_cron:-true}

if [[ "$enable_cron" == "true" ]]; then
  read -p "enable_cron_announce (true/false) [true]: " enable_cron_announce
  enable_cron_announce=${enable_cron_announce:-true}

  read -p "cron_message [cron]: " cron_message
  cron_message=${cron_message:-cron}

  read -p "cron_interval (秒) [60]: " cron_interval
  cron_interval=${cron_interval:-60}
fi

echo ""
echo "=== Monitor 設定 ==="
read -p "enable_monitor (true/false) [true]: " enable_monitor
enable_monitor=${enable_monitor:-true}

if [[ "$enable_monitor" == "true" ]]; then
  read -p "mgmt_channel_id (CXXXXXXXXXX): " mgmt_channel_id

  read -p "ok_message [Dify's up!]: " ok_message
  ok_message=${ok_message:-"Dify's up!"}

  read -p "down_alert_message [Dify's down!]: " down_alert_message
  down_alert_message=${down_alert_message:-"Dify's down!"}

  read -p "monitor_interval (秒) [60]: " monitor_interval
  monitor_interval=${monitor_interval:-60}
fi

echo ""
echo "設定ファイルを作成中..."

{
echo "slack_bot_token: ${slack_bot_token}"
echo "slack_app_token: ${slack_app_token}"
echo ""
echo "dify_scheme: ${dify_scheme}"
echo "dify_endpoint: ${dify_endpoint}"
echo "dify_api_key: ${dify_api_key}"
echo ""
echo "enable_cron: ${enable_cron}"

if [[ "$enable_cron" == "true" ]]; then
  echo "enable_cron_announce: ${enable_cron_announce}"
  echo "cron_message: \"${cron_message}\""
  echo "cron_interval: ${cron_interval}"
fi

echo ""
echo "enable_monitor: ${enable_monitor}"

if [[ "$enable_monitor" == "true" ]]; then
  echo "mgmt_channel_id: \"${mgmt_channel_id}\""
  echo "ok_message: \"${ok_message}\""
  echo "down_alert_message: \"${down_alert_message}\""
  echo "monitor_interval: ${monitor_interval}"
fi

} > "$OUTPUT_FILE"

echo "完了: ${OUTPUT_FILE} を作成しました！"