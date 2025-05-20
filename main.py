# -*- mode: python ; coding: utf-8 -*-
from minio.error import S3Error
from pathlib import Path
import sys
import logging
from datetime import datetime, timedelta
from urllib3 import PoolManager
from minio import Minio
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_file_info(file_path: str) -> None:
    """
    获取文件的大小和文件类型，并打印相关信息。

    :param file_path: 文件的路径
    """
    # 使用 Path 来解析文件后缀（文件类型）
    file = Path(file_path)

    if not file.is_file():
        logging.info("提供的路径不是一个有效的文件。")
        return

    file_size = file.stat().st_size  # 获取文件大小（字节）
    file_type = file.suffix  # 获取文件后缀名（即文件类型）

    logging.info(f"文件大小: {file_size} 字节")
    logging.info(f"文件类型: {file_type}")


def upload_file_to_minio(file_path: str, bucket_name: str = "exchange-module") -> None:
    """
    将指定文件上传到 MinIO 的指定桶中，并使用日期目录和时间戳重命名文件。

    :param file_path: 文件路径
    :param bucket_name: 目标桶名称
    """
    # 创建 Path 对象
    file = Path(file_path)

    if not file.is_file():
        logging.error("提供的路径不是一个有效的文件。")
        return

    # 自定义 HTTP 客户端，设置连接和读取超时
    http_client = PoolManager(
        timeout=5.0,  # 5秒超时
        retries=1
    )

    # MinIO 连接配置（请根据实际情况修改）
    # client = Minio(
    #     "cloud-minio-10-5-1-236:8080",  # MinIO 服务地址
    #     access_key="VgqABlPoZYMFZOsR89gh",
    #     secret_key="YXL3c6Kd7bslsyXGOQwFAEFBypi9GkfkYPezcY8I",
    #     secure=False,  # 使用 HTTPS
    #     http_client=http_client
    # )

    client = Minio(
        "cloud-minio-data-10-5-3-176:8082",  # MinIO 服务地址
        access_key="igiylPwL3gz8CLrT0M1a",
        secret_key="pLNbAHRj1nT0pz3Bsj9M3In15GbXnMDqblUbFTuS",
        secure=False,  # 使用 HTTPS
        http_client=http_client
    )

    try:
        logging.info("正在检查桶是否存在...")
        if not client.bucket_exists(bucket_name):
            logging.info("桶不存在，正在创建...")
            client.make_bucket(bucket_name)
            logging.info(f"Bucket '{bucket_name}' 已创建")
        else:
            logging.info(f"Bucket '{bucket_name}' 已存在")

        # 获取当前日期和时间
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")  # 年月日
        time_str = now.strftime("%H%M%S")  # 时分秒

        # 构造对象名：原文件名_时间戳.后缀
        original_name = file.stem  # 原始文件名（不含后缀）
        suffix = file.suffix       # 文件后缀
        new_object_name = f"{original_name}-{time_str}{suffix}"

        # 构造完整对象路径（MinIO 中的“目录”结构）
        object_name = f"upload/{date_str}/{new_object_name}"

        # 上传文件
        client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=str(file),
        )
        logging.info(f"文件 '{file_path}' 成功上传到桶 '{bucket_name}' 中，对象名为 '{object_name}'")
        return send_dapi_server(object_name)
    except S3Error as err:
        logging.error(f"上传失败: {err}")


def send_mail_server(headers, link, password):
    add_mail_url = "http://10.5.3.176:8082/api/xiang-mail/mail/submit"
    add_mail_data = {
        "mailTmpId": "2025401930861579817",
        "subject": "2024_733需求-测试",
        "fillValueList": [
            {
                "input": "userName",
                "$cellEdit": "true",
                "$index": 0,
                "index": "",
                "value": "测试老师你好"
            },
            {
                "input": "taskName",
                "$cellEdit": "true",
                "$index": 1,
                "index": "",
                "value": "2024-773需求-测试任务"
            },
            {
                "input": "mail_file_link",
                "$cellEdit": "true",
                "$index": 2,
                "index": "",
                "value": link
            },
            {
                "input": "mail_file_code",
                "$cellEdit": "true",
                "$index": 3,
                "index": "",
                "value": password
            }
        ],
        "consigneeList": [
            "array_xiangxiang@163.com"
        ],
        "recipientsList": [],
        "queryTime": "",
        "id": "2025709288553429959",
        "createUser": "202411141129378390",
        "updateUser": -1,
        "updateTime": "",
        "status": 1,
        "isDeleted": 0,
        "recipients": "[]",
        "fileUrl": "null",
        "fileUrlList": [],
        "fileName": "",
        "mailLogId": -1,
        "$index": 0,
        "$mailTmpId": "数据交付 对内 链接 data_alarm"
    }

    try:
        # 发送 POST 请求
        mail_res = requests.post(
            url=add_mail_url,
            headers=headers,
            json=add_mail_data  # 使用 json 参数自动设置 Content-Type: application/json
        )

        # 打印响应内容（调试用）
        logging.info("新增邮件，请求状态码: %s", mail_res.status_code)
        logging.info("新增邮件，请求响应内容: %s", mail_res.text)

        mail_data = mail_res.json()
        mail_succ = mail_data.get('success')

        if mail_succ is True:
            logging.info('新增邮件成功, 邮件信息')
            send_mail_url = "http://10.5.3.176:8082/api/xiang-mail/mail/send-mail"
            try:
                send_mail_res = requests.post(
                    url=send_mail_url,
                    headers=headers,
                    json=add_mail_data  # 使用 json 参数自动设置 Content-Type: application/json
                )
                # 打印响应内容（调试用）
                logging.info("发送邮件，请求状态码: %s", send_mail_res.status_code)
                logging.info("发送邮件，请求响应内容: %s", send_mail_res.text)

                send_mail_res_data = send_mail_res.json()
                send_succ = send_mail_res_data.get('success')

                if send_succ is True:
                    logging.info('发送邮件成功，请注意查收，收件人：%s', add_mail_data.get('consigneeList'))
                else:
                    logging.error('发送邮件失败')


            except requests.exceptions.RequestException as e:
                logging.info("发送邮件失败: %s", e)


        else:
            logging.error("新增邮件失败")
            return
    except requests.exceptions.RequestException as e:
        logging.info("新增邮件失败: %s", e)


def send_dapi_server(upload_file_path):
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
        logging.info("登录认证，请求状态码: %s", response.status_code)
        logging.info("登录认证，请求响应内容: %s", response.text)

        access_token = None

        # 解析 JSON 并提取 access_token
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            if access_token:
                logging.info("获取到的 access_token: %s", access_token)
            else:
                logging.info("未找到 access_token 字段")
        else:
            print("请求失败，请检查服务是否正常运行或凭据是否正确")

        if access_token:
            # 要请求的接口地址
            send_dapi_exchange_url = "http://10.5.3.176:8082/api/xiang-exchange/exchange-log/add-share"

            # 请求头
            headers = {
                'Authorization': 'Basic c2FiZXI6c2FiZXJfc2VjcmV0',
                'Xiang-Auth': f'bearer {access_token}'
            }

            now = datetime.now()
            valid_period = (now + timedelta(days=4)).replace(hour=0, minute=0, second=0, microsecond=0)
            valid_period_str = valid_period.strftime("%Y-%m-%d %H:%M:%S")

            # 请求数据体
            data = [{
                "filePath": upload_file_path,
                "validPeriod": valid_period_str,
                "numberOfDown": 1
            }]

            try:
                # 发送 POST 请求
                exchange_response = requests.post(
                    url=send_dapi_exchange_url,
                    headers=headers,
                    json=data  # 使用 json 参数自动设置 Content-Type: application/json
                )

                # 打印响应状态码和内容
                logging.info("获取分享链接，请求状态码: %s", exchange_response.status_code)
                logging.info("获取分享链接，请求响应内容: %s", exchange_response.text)

                link_res = exchange_response.json()
                link_succ = link_res.get('success')

                if link_succ is True:
                    link_data = link_res.get('data')
                    link_data_share_link = link_data.get('shareLink')
                    link_data_pass_code = link_data.get('passCode')
                    # link_data_file_path = link_data.get('filePath')
                    # link_data_valid_period = link_data.get('validPeriod')
                    # link_data_number_of_down = link_data.get('numberOfDown')
                    logging.info("生成链接成功，链接地址：【%s】， 提取码：【%s】，", link_data_share_link, link_data_pass_code)
                    send_mail_server(headers, link_data_share_link, link_data_pass_code)



                else:
                    logging.error("生成链接失败")
                    return None

                # 返回响应对象，供后续处理使用
                return exchange_response

            except requests.exceptions.RequestException as e:
                logging.error("请求过程中发生错误: %s", e)
                return None

    except requests.exceptions.RequestException as e:
        logging.info("请求过程中发生错误: %s", e)


# 从命令行参数获取路径
if __name__ == "__main__":

    input_path = ""
    if len(sys.argv) < 2:
        print("请提供一个路径作为参数。")
        input_path = input("请输入路径: ")
    else:
        input_path = sys.argv[1]

    get_file_info(input_path)
    upload_file_to_minio(input_path)
