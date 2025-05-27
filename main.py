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

local_path = "/Users/xiang/Desktop/dapi_exchange/"
linux_path = "/share/infa_shared/TgtFiles/bi/liscron/"

file_path = linux_path

local_minio_url = "cloud-minio-data-10-5-3-176:8082"
linux_minio_url = "10.5.3.178:9000"

minio_url = linux_minio_url

# 2025709288553429959 再保数据，好管家和非趸交团险短险数据            每月月初再保数据.zip
# 2025310044132876668 上分统计数据                               sftjsj-1.xlsx
# 2025310064655143366 保单明细打印数据                            bdmxdy-1.xlsx
# 2025310078034332520 每月初个单万能险账户价值数据                  万能险账户价值数据_个单.zip
# 2025310099331360202 每月初准备金数据                            准备金数据.zip
# 2025312234481240576 每月初理赔金数据                            赔案准备金数据.zip


# 邮件信息 源数据
mail_info = [
    {
        "id": 1,
        "mailId": 2025709288553429959,
        "filePath": f"{file_path}每月月初再保数据.zip"
    },
    {
        "id": 2,
        "mailId": 2025310044132876668,
        "filePath": f"{file_path}sftjsj-1.xlsx"
    },
    {
        "id": 3,
        "mailId": 2025310064655143366,
        "filePath": f"{file_path}bdmxdy-1.xlsx"
    },
    {
        "id": 4,
        "mailId": 2025310078034332520,
        "filePath": f"{file_path}万能险账户价值数据_个单.zip"
    },
    {
        "id": 5,
        "mailId": 2025310099331360202,
        "filePath": f"{file_path}准备金数据.zip"
    },
    {
        "id": 6,
        "mailId": 2025312234481240576,
        "filePath": f"{file_path}赔案准备金数据.zip"
    }
]


def get_mail_info_by_id(input_num_id: str, mail_info_list: list) -> dict:
    """
    根据 input_num 查找 mail_info 中对应的对象。

    :param input_num_id: 要查找的 id 值
    :param mail_info_list: 邮件信息列表
    :return: 匹配的 mail_info 对象，未找到时返回 None
    """
    for mail in mail_info_list:
        if str(mail.get("id")) == input_num_id:
            return mail
    return None


def get_file_info(verify_file: dict) -> None:
    """
    获取文件的大小和文件类型，并打印相关信息。

    :param verify_file: 邮件信息
    """
    # 使用 Path 来解析文件后缀（文件类型）
    file_path = verify_file.get("filePath")
    file = Path(file_path)

    if not file.is_file():
        logging.info("提供的路径不是一个有效的文件。")
        return

    file_size = file.stat().st_size  # 获取文件大小（字节）
    file_type = file.suffix  # 获取文件后缀名（即文件类型）

    logging.info(f"文件大小: {file_size} 字节")
    logging.info(f"文件类型: {file_type}")


def upload_file_to_minio(send_mail_info: dict, bucket_name: str = "exchange-module") -> None:
    """
    将指定文件上传到 MinIO 的指定桶中，并使用日期目录和时间戳重命名文件。

    :param send_mail_info: 邮件信息
    :param bucket_name: 目标桶名称
    """
    # 创建 Path 对象
    file_path = send_mail_info.get("filePath")
    mail_id = send_mail_info.get("mailId")
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
    client = Minio(
        minio_url,  # MinIO 服务地址
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

        send_file_mail_info = {
            **send_mail_info,
            "file_object": object_name  # 新增 file_object 元素
        }

        return send_dapi_server(file_mail_info=send_file_mail_info)
    except S3Error as err:
        logging.error(f"上传失败: {err}")


def update_mail_and_send(file_mail: dict, headers, link: str, password: str):
    mail_id = file_mail.get("mailId")

    """
    调用接口，获取详细信息，供发送邮件使用
    """
    detail_mail_url = f"http://10.5.3.176:8082/api/xiang-mail/mail/detail?id={mail_id}"
    detail_mail = requests.get(
        url=detail_mail_url,
        headers=headers
    )

    # 打印响应内容（调试用）
    logging.info("获取邮件详情，请求状态码: %s", detail_mail.status_code)
    logging.info("获取邮件详情，请求响应内容: %s", detail_mail.text)

    detail_mail_info = detail_mail.json()
    detail_mail_succ = detail_mail_info.get('success')

    if detail_mail_succ is True:
        logging.info('查询邮件详情成功')
        logging.info(detail_mail_info)
        detail_mail_info = detail_mail_info.get('data')
        newFillValueList = [
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
        ]
        detail_mail_info["fillValueList"] = newFillValueList
        logging.info(detail_mail_info)

    """
    调用接口，修改当前最新的文件信息
    """
    add_mail_url = "http://10.5.3.176:8082/api/xiang-mail/mail/submit"
    add_mail_data = detail_mail_info
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


def send_dapi_server(file_mail_info):
    upload_file_path = file_mail_info.get("file_object")
    """
    鉴权部分，使用 api 用户进行操作
    """
    get_token_url = (
        "http://10.5.3.176:8082/api/xiang-auth/oauth/token"
        "?tenant_id=000000"
        "&username=api"
        "&password=a69292766d57ab36b4e072ef1f0a1248"
        "&grant_type=password"
        "&scope=all"
    )
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
            """
            调用接口，生成 Url 分享地址，获取上传的文件
            策略： 3 天内，下载 1 次
            """
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
                    update_mail_and_send(file_mail=file_mail_info,
                                         headers=headers,
                                         link=link_data_share_link,
                                         password=link_data_pass_code)

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

    input_num = ""
    if len(sys.argv) < 2:
        print("请提供一个路径作为参数。")
        input_num = input("请输入路径: ")
    else:
        input_num = sys.argv[1]

    # 根据 input_num 的值匹配  mail_info 的id，如果匹配到了，就返回匹配到的 json 对象
    matched_mail_info = get_mail_info_by_id(input_num, mail_info)
    if matched_mail_info:
        print(f"找到匹配的 mail_info 对象: {matched_mail_info}")
    else:
        raise ValueError("未找到匹配的对象")

    get_file_info(verify_file=matched_mail_info)
    upload_file_to_minio(send_mail_info=matched_mail_info)