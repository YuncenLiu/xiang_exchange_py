import requests
from datetime import datetime
import json

# 获取当前时间，格式为 'YYYY-MM-DD HH:MM:SS'
date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"当前时间: {date}")

# 定义请求URL
get_token_url = (
    "http://10.5.3.176:8082/api/xiang-auth/oauth/token"
    "?tenant_id=000000"
    "&username=api"
    "&password=a69292766d57ab36b4e072ef1f0a1248"
    "&grant_type=password"
    "&scope=all"
)

# 设置请求头
headers = {
    'Authorization': 'Basic c2FiZXI6c2FiZXJfc2VjcmV0'
}

# 发送 POST 请求
try:
    response = requests.post(get_token_url, headers=headers)

    # 打印响应内容（调试用）
    print("响应状态码:", response.status_code)
    print("响应内容:", response.text)

    # 解析 JSON 并提取 access_token
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        if access_token:
            print("获取到的 access_token:", access_token)
        else:
            print("未找到 access_token 字段")
    else:
        print("请求失败，请检查服务是否正常运行或凭据是否正确")

except requests.exceptions.RequestException as e:
    print("请求过程中发生错误:", e)
