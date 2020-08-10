# daily_health_script

### 介绍
NUIST健康日报填写脚本

### 运行

**必备工具**
- python3
- requests (python的包)
- my-fake-useragent (python的包)

包的安装方式: `python -m pip install requests my-fake-useragent`

**运行方法**

![初次运行](pics/1.png)

- 第一次运行, 输入`python auto_healthy.py loop` 或者 `python auto_healthy.py once`来生成配置文件.
    - 配置文件在上述帮助信息中会说明位置.
    - 配置文件的扩展名是json
    - 另一个log结尾的是日志文件
- 打开配置文件(上述为C:\\Users\\zyx1\\daily_health.json)
![配置文件内容](pics/2.png)
    - 由于方便阅读, 手动分了行.
    - `username`: [学校网站](http://my.nuist.edu.cn)的用户名
    - `password`: 学校网站的密码
    - `default_log_level`: 默认的日志等级: 0-5对应`debug`, `info`, `warn`, `error`, `fatal`和`disable`. 默认的是1(info)
    - `postTime`: 发送请求的时间, 可以是单个时间, 可以是逗号隔开的时间, 格式是HH:MM, 注意逗号和冒号是英文符号, 中间没有空格. (loop模式)
    - `run_and_loop`: 在设定循环提交之前先提交一次请求. (loop模式)
    - `note`: 就是note信息嘛... 这个不影响的2333...
    - 配置好的json文件大概长成这个样子:
![配置好的配置文件](pics/3.png)
- 配置文件配置好, **保存**, 然后再运行刚才的`python auto_healthy.py loop` 或 `python auto_healthy.py once`, 就可以正常运行了(前提是账号密码啥的没问题)

#### 提醒

有些设备可能没办法安装`my-fake-useragent`模块, duck不必担心.

py文件里面, 有一行是`from my_fake_useragent import UserAgent as UA`, 删掉, 后面有一行`self.s.headers['User-Agent'] = UA().random()`改成你想换的`User-Agent`就可以了.

![位置](pics/4.png)

比如
 `self.s.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"`

 ## **如果代码有问题的话, 可以把最后出问题的log文件截图[发给我](mailto:happy.rabbit.yy@outlook.com)**