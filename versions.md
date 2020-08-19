## 版本信息

### 当前最新版本为 1.0.2

[![](https://img.shields.io/badge/-return%20to%20README.md-blueviolet)](README.md "返回README.md")

### 1.0.2 更新内容

项目 |内容
:--: |:--:
更新日期 | 2020年8月19日
是否有重大更新 | ![](https://img.shields.io/badge/-no-informational "否")
版本状态 | ![](https://img.shields.io/badge/-newest-brightgreen "最新")

**更新内容**:

- 新增了一个`class`, 叫做`SelfAbort`
  - 用来手动`raise`错误并且进行重试处理
  - 继承`Exception`
  - 被定义为一种异常
- 调整了一下部分log的输出顺序和重试终止次数

**此版本的变量**: 

> 和[上一版本](#1-0-1)的[变量](#1-0-1-vars)一致

---

### <span id="1-0-1">1.0.1 更新内容</span>

> *前言*: 由于太懒了所以懒得把之前的改成1.0.0了, 索性直接合并发布好了(

项目 |内容
:--: |:--:
更新日期 | 2020年8月18日
是否有重大更新 | ![](https://img.shields.io/badge/-yes-important "是")
版本状态 | ![](https://img.shields.io/badge/-newest-brightgreen "最新")

**更新内容**:

- [x] 修改原有的主页地址和登录地址
- [x] 原有的登录方式失效, 修改为最新登录方式
- [x] 可以检测是否需要验证码
  - 目前验证码还无法自动识别
  - 而且也没有显示验证码的代码
  - **大概**下个版本会追加显示验证码的功能 ~~(**大概**)~~

<span id="1-0-1-vars">**此版本的变量**:</span>

静态变量 | 内容
:--: | :--:
主页 | [`http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2F`](http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2F)
登录网址 | `http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2Findex.portal`
表单请求地址 | `http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start`
log文件夹 | `%UserProfile%\pyLogs\`(windows) 或 `$HOME/pylogs/`(Linux)
log文件名 | `auto_commit_daily_healthy.log`
config文件夹 | `%UserProfile%\`(windows) 或 `$HOME/`(Linux)
config文件名 | `daily_health.json`

**备注**:

标记为*重大更新*的原因是:
- 学校今天部署了统一认证系统
- 原有的页面现在已经重定向
- 原有的认证方式已经失效
- 现有的认证方式有可能会登录失败
  - 登录失败的原因是
  - 可能会需要验证码
  - 如果登录失败, 会在log里面显示失败原因 ~~(大概)~~
- 验证码目前还无法自动识别或者显示
- 此版本的Linux端还没进行验证
  - 可能会出现问题

---

### 1.0.0 更新内容

**此版本的信息**:

项目 |内容
:--: |:--:
更新日期 | 2020年8月18日
是否有重大更新 | ![](https://img.shields.io/badge/-yes-important "是")
版本状态 | ![](https://img.shields.io/badge/-out%20of%20date-inactive "过时")

**更新内容**:

- [x] 自动登录主页, 并且自动填写信息并提交
- [x] log等级的自定义
- [x] 较为详尽的log输出
- [x] 文件内加入版本号, 方便查看

**此版本的变量**:

静态变量 | 内容
:--: | :--:
主页 | [`http://my.nuist.edu.cn`](http://my.nuist.edu.cn)
登录网址 | `http://my.nuist.edu.cn/userPasswordValidate.portal`
表单请求地址 | `http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start`
log文件夹 | `%UserProfile%\pyLogs\`(windows) 或 `$HOME/pylogs/`(Linux)
log文件名 | `auto_commit_daily_healthy.log`
config文件夹 | `%UserProfile%\`(windows) 或 `$HOME/`(Linux)
config文件名 | `daily_health.json`

**备注**:

无