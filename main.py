import json
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

SLACK_BOT_TOKEN="xoxb-..."
SLACK_APP_TOKEN="xapp-..."
DIFY_ENDPOINT="IP or FQDN"
DIFY_API_KEY_DEFAULT="app-..."
DIFY_API_KEY_APP1="app-..."
DIFY_API_KEY_APP2="app-..."
DIFY_API_KEY_APP3="app-..."
channel_apikeys={"C...":DIFY_API_KEY_APP1,"C...":DIFY_API_KEY_APP2,"C...":DIFY_API_KEY_APP3}
ai_thread_ts_list = set()
file_type_dict = {"document":["txt","md","mdx","markdown","pdf","html","htm","xlsx","xls","doc","docx","csv","eml","msg","pptx","ppt","xml","epub"],
                  "image":["png","jpg","jpeg","gif","webp","svg"]}
FILE_DIR = "/root/imgs/"
ai_thread_ts_list = set()
file_type_dict = {"document":["txt","md","mdx","markdown","pdf","html","htm","xlsx","xls","doc","docx","csv","eml","msg","pptx","ppt","xml","epub"],
                  "image":["png","jpg","jpeg","gif","webp","svg"]}
FILE_DIR = "/root/imgs/"

def extractFilePaths(answer:str):
    results = []
    for ext in ["png","wav"]:
        results += re.findall(r'\[(.*?\.'+ext+r')\]',answer)
    if len(results) > 0:
        return results
    else:
        return None

app = App(token=SLACK_BOT_TOKEN)

# ボットのユーザーIDを取得
bot_user_id = app.client.auth_test()["user_id"]
conversation_ids = {}

def upload_to_slack(filename:str,data:bytes):
    try:
        new_file_place = app.client.files_getUploadURLExternal(filename=filename,length=len(data))
        if new_file_place['ok']:
            response_post_file = requests.post(
                                url=new_file_place['upload_url'],
                                data=data
                            )
            response_complete_file = app.client.files_completeUploadExternal(files=[{"id":new_file_place['file_id']}])
            answer_str = response_complete_file["files"][0]["permalink"]
            return answer_str
    except:
        return None

def upload_to_dify(user,filename:str,filedata:bytes,mimetype:str):
    files = {'file': (filename, filedata, mimetype)}
    data = {'user': user}
    url = f'http://{DIFY_ENDPOINT}/v1/files/upload'
    headers = {'Authorization': 'Bearer '+DIFY_API_KEY_DEFAULT}
    response = requests.post(url,headers=headers, files=files,data=data)
    return response

def download_from_slack(url:str) -> bytes:
    headers = {'Authorization': 'Bearer '+SLACK_BOT_TOKEN}
    response = requests.get(url,headers=headers)
    return response.content

def talk(event, say):
    if event and 'text' in event:
        dify_api_key = DIFY_API_KEY_DEFAULT
        if "channel" in event and event["channel"] in channel_apikeys:
            dify_api_key = channel_apikeys[event["channel"]]
        url = f'http://{DIFY_ENDPOINT}/v1/chat-messages'  # Dify API endpoint
        user = event['user']
        query = event['text'].replace(
            f"<@{bot_user_id}>", "").strip()  # メンション部分を削除
        input_filepaths =[]
        if "files" in event:
            for fileinfo in event["files"]:
                input_filepaths.append(fileinfo["url_private"])
        print("files",input_filepaths)
        input_files = []
        for input_filepath in input_filepaths:
            filename = input_filepath.split("/")[-1]
            filedata = download_from_slack(input_filepath)
            response = upload_to_dify(user,filename,filedata,"image/png")
            response_json = json.loads(response.text)
            file_type = None
            for ft in file_type_dict:
                if filename.split(".")[-1] in file_type_dict[ft]:
                    file_type=ft
            if file_type is None:
                say(f"{filename} は対応していないフォーマットのファイルです。")
                continue
            file_uuid = response_json["id"]
            file = {"transfer_method":"local_file","type":file_type,"upload_file_id":file_uuid}
            input_files.append(file)
        print("input_files",input_files)

        thread_ts = None
        if "thread_ts" in event:
            thread_ts = event["thread_ts"]
        else:
            thread_ts = event["ts"]
        ai_thread_ts_list.add(thread_ts)

        headers = {
            'Authorization': f'Bearer {dify_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'query': query,
            'response_mode': 'blocking',
            'user': user,
            'conversation_id': conversation_ids[thread_ts] if thread_ts in conversation_ids else "",
            'inputs': {},
            'files':input_files
        }
        if thread_ts is None:
            say("Responding...")
        else:
            say("Responding...",thread_ts = thread_ts)
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        print(response_data)
        if 'answer' in response_data:
            answer_str = "Error: No answer"
            answer = response_data['answer']
            print(answer)
            filePaths = extractFilePaths(answer)
            print("filepaths",filePaths)
            if filePaths is None:
                answer_str = response_data['answer']
            else:
                answer_str = ""
                for imgId, filepath in enumerate(filePaths):
                    extention = filepath.split(".")[-1]
                    file_data = open(FILE_DIR+filepath,"rb").read()
                    answer_str += upload_to_slack(f"result{imgId}.{extention}",file_data) + "\n"
            if thread_ts is None:
                say(answer_str)
            else:
                say(answer_str,thread_ts = thread_ts)
                if 'conversation_id' in response_data:
                    conversation_ids[thread_ts] = response_data['conversation_id']
        else:
            say(f"Dify APIからの予期しないレスポンス: {response_data}")
    else:
        say("メッセージの内容を取得できませんでした。")

@app.event("message")
def handle_message(event, say):
    print("message",event)
    if "thread_ts" in event and event["thread_ts"] in ai_thread_ts_list:
        talk(event,say)
    elif "channel_type" in event and event["channel_type"]:
        talk(event,say)

@app.event("app_mention")
def handle_app_mention(event, say):
    print("app_mention",event)
    talk(event,say)

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
