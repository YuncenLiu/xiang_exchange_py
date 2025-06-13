## 将 py 构建成 shell 脚本

```shell
pyinstaller --onefile dapi_exchange_main.py
```


Linux 上如果无法执行，报错内容：
```
ModuleNotFoundError: No module named '_ctypes'
```

大概率缺少C库
```shell
yum install libffi-devel
```


## 部署在服务器中

- 10.5.3.176 测试

- 10.6.74.161 生产


```shell
mkdir -p /share/infa_shared/TgtFiles/dapi/exchange/
cd /share/infa_shared/TgtFiles/dapi/exchange/

# 上传 dapi_exchange_main_linux_pro

mv dapi_exchange_main_linux_pro dapi-exchange-main
```

