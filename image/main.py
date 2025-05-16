import re
import os
import yaml
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

file_type_dict = {
    "document": [
        "txt",
        "md",
        "mdx",
        "markdown",
        "pdf",
        "html",
        "htm",
        "xlsx",
        "xls",
        "doc",
        "docx",
        "csv",
        "eml",
        "msg",
        "pptx",
        "ppt",
        "xml",
        "epub",
    ],
    "image": ["png", "jpg", "jpeg", "gif", "webp", "svg"],
    "audio": ["mp3", "m4a", "wav", "amr", "mpga"],
    "video": ["mp4", "mov", "mpeg", "webm"],
}


class Secrets:
    def __init__(self):
        secret_filename = os.listdir("/run/secrets/")[0]
        with open("/run/secrets/" + secret_filename) as secret_file:
            self._secrets = yaml.safe_load(secret_file)

    def get_bot_token(self):
        return self._secrets["slack_bot_token"]

    def get_app_token(self):
        return self._secrets["slack_app_token"]

    def get_dify_scheme(self):
        return self._secrets["dify_scheme"]

    def get_dify_endpoint(self):
        return self._secrets["dify_endpoint"]

    def get_dify_api_key(self):
        return self._secrets["dify_api_key"]


class SlackClient:
    def __init__(self, app_token, bot_token):
        self.app_token = app_token
        self.bot_token = bot_token

    def get_my_id(self) -> str:
        headers = {"Authorization": "Bearer " + self.bot_token}
        try:
            response = requests.get(
                url="https://slack.com/api/auth.test", headers=headers
            ).json()
            return response["user_id"]
        except:
            return ""

    def upload(self, file_name: str, file_data: bytes) -> str:
        headers = {"Authorization": "Bearer " + self.bot_token}
        new_file_place = requests.get(
            url="https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            params={"filename": file_name, "length": len(file_data)},
        ).json()
        if not new_file_place["ok"]:
            return ""

        requests.post(url=new_file_place["upload_url"], data=file_data)
        response_complete_file = requests.post(
            url="https://slack.com/api/files.completeUploadExternal",
            headers=headers,
            params={"files": '[{"id":"' + new_file_place["file_id"] + '"}]'},
        ).json()

        if not response_complete_file["ok"]:
            return ""
        return response_complete_file["files"][0]["permalink"]

    def download(self, file_url: str) -> bytes:
        headers = {"Authorization": "Bearer " + self.bot_token}
        response = requests.get(file_url, headers=headers)
        return response.content

    def download_event_files(self, event) -> list[str, str, str]:
        if "files" not in event:
            return []
        input_files = []
        for fileinfo in event["files"]:
            url = fileinfo["url_private"]
            filename = url.split("/")[-1]
            mimetype = fileinfo["mimetype"]
            filedata = self.download(fileinfo["url_private"])
            input_files.append((filename, filedata, mimetype))
        return input_files

    def delete_replies(self, channel, thread_ts) -> None:
        headers = {"Authorization": "Bearer " + self.bot_token}
        response = requests.get(
            f"https://slack.com/api/conversations.replies?channel={channel}&ts={thread_ts}",
            headers=headers,
        )
        json = response.json()
        if "messages" not in json:
            return

        for m in json["messages"]:
            requests.post(
                f"https://slack.com/api/chat.delete?channel={channel}&ts={m["ts"]}",
                headers=headers,
            )


class DifyClient:
    def __init__(self, scheme, endpoint, api_key):
        self.scheme = scheme
        self.endpoint = endpoint
        self.api_key = api_key

    def upload(self, user, filename: str, filedata: bytes, mimetype: str) -> dict:
        headers = {"Authorization": "Bearer " + self.api_key}
        files = {"file": (filename, filedata, mimetype)}
        data = {"user": user}
        url = f"{self.scheme}://{self.endpoint}/v1/files/upload"
        response = requests.post(url, headers=headers, files=files, data=data)
        return response.json()

    def download(self, file_url) -> bytes:
        headers = {"Authorization": "Bearer " + self.api_key}
        return requests.get(url=file_url, headers=headers).content

    def query(self, data):
        dify_chat_url = f"{self.scheme}://{self.endpoint}/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(dify_chat_url, headers=headers, json=data).json()
        return response


class SlackDifyConnector:
    def __init__(self, secrets):
        self.slack = SlackClient(secrets.get_app_token(), secrets.get_bot_token())
        self.dify = DifyClient(
            secrets.get_dify_scheme(),
            secrets.get_dify_endpoint(),
            secrets.get_dify_api_key(),
        )
        self.conversation_ids = {}

    def extract_file_urls(self, answer: str) -> dict:
        result = {}
        for file_name, file_url in re.findall(r"\!\[(.*)\]\((.*)\)", answer):
            result[file_name] = file_url
        return result

    def get_input_files(self, event) -> list[dict]:
        input_files = []
        for filename, filedata, mimetype in self.slack.download_event_files(event):
            extention = filename.split(".")[-1].lower()
            dify_file_type = None
            for ft in file_type_dict:
                if extention in file_type_dict[ft]:
                    dify_file_type = ft
                    break
            if dify_file_type is None:
                dify_file_type = "custom"
            try:
                dify_response = self.dify.upload(
                    event["user"], filename, filedata, mimetype
                )
                dify_file_uuid = dify_response["id"]
            except:
                raise Exception("Failed to upload files to Dify")
            file = {
                "transfer_method": "local_file",
                "type": dify_file_type,
                "upload_file_id": dify_file_uuid,
            }
            input_files.append(file)
        return input_files

    def talk(self, event, say):
        if event is None or not "text" in event:
            return
        user = event["user"]
        query = event["text"].replace(f"<@{self.slack.get_my_id()}>", "").strip()
        thread_ts = event["ts"]
        if "thread_ts" in event:
            thread_ts = event["thread_ts"]
        if "cleanclean" in query:
            self.slack.delete_replies(event["channel"], thread_ts)
        if len(query) == 0:
            query = "(empty)"
        try:
            input_files = self.get_input_files(event)
        except:
            pass
        print("input_files", input_files)
        conversation_id = ""
        if thread_ts in self.conversation_ids:
            conversation_id = self.conversation_ids[thread_ts]
        full_query = {
            "query": query,
            "response_mode": "blocking",
            "user": user,
            "conversation_id": conversation_id,
            "inputs": {
                "slack_channel": event["channel"],
                "slack_channel_type": event["channel_type"],
                "slack_timestamp": event["ts"],
                "slack_thread_ts": thread_ts,
                "slack_team": event["team"],
            },
            "files": input_files,
        }

        say("Responding...", thread_ts=thread_ts)
        dify_response = self.dify.query(full_query)
        print("dify_response", dify_response)
        if "answer" not in dify_response:
            say(
                f"Unexprected response from Dify API: {dify_response}",
                thread_ts=thread_ts,
            )
            return
        answer: str = dify_response["answer"]

        file_urls = self.extract_file_urls(answer)
        if file_urls != {}:
            for file_name in file_urls:
                file_data = self.dify.download(file_urls[file_name])
                dify_file_link = file_urls[file_name]
                slack_file_link = self.slack.upload(file_name, file_data)
                if slack_file_link == "":
                    answer = answer.replace(dify_file_link, "")
                    answer += f"Failed to upload {file_name} to Slack\n"
                    continue
                answer = answer.replace(dify_file_link, slack_file_link)

        say(answer, thread_ts=thread_ts)
        if thread_ts is not None and "conversation_id" in dify_response:
            self.conversation_ids[thread_ts] = dify_response["conversation_id"]


if __name__ == "__main__":
    mentioned_thread_ts = set()
    secrets = Secrets()
    sdc = SlackDifyConnector(secrets)
    app = App(token=secrets.get_bot_token())

    @app.event("app_mention")
    def handle_app_mention(event, say):
        print("app_mention", event)
        sdc.talk(event, say)
        thread_ts = event["ts"]
        if "thread_ts" in event:
            thread_ts = event["thread_ts"]
        mentioned_thread_ts.add(thread_ts)

    @app.event("message")
    def handle_message(event, say):
        print("message", event)
        if "thread_ts" in event and event["thread_ts"] in mentioned_thread_ts:
            # If in AI threads started by mentions
            sdc.talk(event, say)
        elif "channel_type" in event and event["channel_type"] == "im":
            # If direct message
            sdc.talk(event, say)

    SocketModeHandler(app, secrets.get_app_token()).start()
