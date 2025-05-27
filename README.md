## 将 py 构建成 shell 脚本

```shell
pyinstaller --onefile main.py
```


Linux 上如果无法执行，报错内容：
```
ModuleNotFoundError: No module named '_ctypes'
```

大概率缺少C库
```shell
yum install libffi-devel
```