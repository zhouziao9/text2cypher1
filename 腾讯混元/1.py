import requests
import json

# 定义 API 的 URL
url = 'https://open.hunyuan.tencent.com/openapi/v1/agent/chat/completions'

# 定义请求头
headers = {
    'X-Source': 'openapi',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer f6UFVkmImKlhPL3yeraS3Ki0CwGwWIMT'
}
# 定义请求体
data = {
    "assistant_id": "SDSzT6KAxe8k",
    "user_id": "SDSzT6KAxe8k",
    "stream": False,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "生成去张家口旅行的计划"
                }
            ]
        }
    ]
}

# 将请求体转换为 JSON 格式的字符串
json_data = json.dumps(data)

# 发送 POST 请求
response = requests.post(url, headers=headers, json=data)  # 使用 json 参数自动设置正确的 Content-Type

# 打印响应内容
print(response.text)