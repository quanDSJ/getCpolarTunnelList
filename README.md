# getCpolarTunnelList
一键获取cpolar中的所有隧道信息脚本
使用cpolar中的免费域名时它不是一直不变的，此脚本解决登录cpolar看查域名并打开的繁琐步骤

- 食用方式🤤

再config文件中的loginCpolar.json里填入自己的用户名和密码即可使用

- 自动跳转

可在loginCpolar.json文件 ` AUTO_OPEN_TUNNEL ` 中添加要自动跳转的隧道名（http，https），一键跳转至浏览器并自动打开指定url

- 环境安装脚本
```python

pip install requests beautifulsoup4PIP install requests beautifulsoup4

```

- windows可执行程序说明 :
在 ` getCpolarTunnelList_win.zip ` 是windows可执行程序，解压即可运行

json格式：
```json
    "CPOLAR_EMAIL": "you_mail",
    "CPOLAR_PASSWORD": "you_password",
    "AUTO_OPEN_TUNNEL": "you_open_name",

    "LOGIN_URL": "https://dashboard.cpolar.com/login",“LOGIN_URL”:“https://dashboard.cpolar.com/login”,
    "AFTER_LOGIN_URL": "https://dashboard.cpolar.com/get-started",“AFTER_LOGIN_URL”:“https://dashboard.cpolar.com/get-started”,
    "TARGET_URL": "https://dashboard.cpolar.com/status"“TARGET_URL”:“https://dashboard.cpolar.com/status”
```
