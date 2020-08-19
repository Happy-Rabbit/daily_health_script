# -*- coding: utf-8 -*-

import time, os, inspect, random, threading, sys, json, copy

__file_version__ = "1.0.2"
__file_version_tuple__ = (1, 0, 2)
__license__ = "MIT"
__author__ = "Happy-Rabbit"
__last_update_date__ = "2020/08/19"

username    :str    =   ''
password    :str    =   ''
userData    :dict   =   {"username":    username, 
                         "password":    password, 
                         "captcha":     '',
                         '_eventId':    'submit',
                         'cllt':        'userNameLogin',
                         'lt':          '',
                         'execution':   ''}
userDataList:list   =   []

configFormat:dict   =   {"username":    '',
                         "password":    '',
                         'nickname':    '',
                         'postTime':    '',}
configFile  :str    =   os.path.join(os.getenv('userprofile'), 'multi_health.json') if os.name == 'nt' else os.path.join(os.getenv('HOME'), 'multi_health.json')

indexUrl    :str    =   "http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2F"
loginUrl    :str    =   "http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2Findex.portal"
renderUrl   :str    =   "http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start"

logFolder   :str    =   os.path.join(os.getenv('userprofile'), 'pyLogs') if os.name == 'nt' else os.path.join(os.getenv('HOME'), 'pyLogs')
logFileName :str    =   "auto_commit_multi_healthy.log"

DEBUG       :str    =   "DEBUG"             # Log level 0
INFO        :str    =   "INFO"              # Log level 1
WARN        :str    =   "WARN"              # Log level 2
ERROR       :str    =   "ERROR"             # Log level 3
FATAL       :str    =   "FATAL"             # Log level 4
DISABLE     :str    =   "DISABLE"           # Log level 5
LOG_LIST    :list   =   [DEBUG, INFO, WARN, ERROR, FATAL, DISABLE]
defaultLog  :int    =   1   # Default log level is INFO. in list [0, 1, 2, 3, 4, 5] 0 is DEBUG, 5 is DISABLE

count       :int    =   0
success     :int    =   0
failed      :int    =   0

assert 0 <= defaultLog <= 5, "Error! Wrong default log level!"

def log(level: str, info: str, isPriv: bool = False) -> None:
    global logFolder, logFileName, LOG_LIST, defaultLog
    logFormat = '[{}.{} {}] In function "{}": {}'
    theTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    mSec = str(time.time()).split('.')[-1].ljust(3, '0')[:3]
    funcName = inspect.stack()[2][3]
    os.mkdir(logFolder) if not os.path.isdir(logFolder) else None
    logFile = open(os.path.join(logFolder, logFileName), 'a+', encoding="UTF-8")
    logInfo = logFormat.format(theTime, mSec, level.rjust(5), funcName, info)
    if isPriv:
        print(logInfo, file=logFile, flush=True)
        logFile.close()
        return None
    if level not in LOG_LIST[:defaultLog]:
        print(logInfo, file=logFile, flush=True)
    logFile.close()
    return None

debug = lambda info: log(DEBUG, info)
info  = lambda info: log(INFO, info)
warn  = lambda info: log(WARN, info)
error = lambda info: log(ERROR, info)
fatal = lambda info: log(FATAL, info)
user  = lambda level, info: log(level, info, isPriv=True)

try:
    import js2py
    from requests import Session
    from my_fake_useragent import UserAgent as UA
    from bs4 import BeautifulSoup as BS
    import curses
except Exception as e:
    fatal(repr(e))
    print(e)
    exit(1)

class SelfAbort(Exception):
    def __init__(self, info: str = ""):
        self.info = info
    def __str__(self):
        return self.info

bs = lambda x: BS(x.content, "html.parser")

try:
    tempSession = Session()
    tempCrypto = tempSession.get("http://authserver.nuist.edu.cn/authserver/ids/common/encrypt.js")
    Crypto = js2py.EvalJs()
    Crypto.execute(tempCrypto.text)
    Crypt = Crypto.encryptPassword
except Exception as e:
    fatal(repr(e))

class AutoLogin():
    def __init__(self, username: str, password: str, postTime: str = '09:00'):
        global userData, Crypt
        try:
            assert postTime, "Error! postTime is empty!"
            assert username, "Error! username is empty!"
            assert password, "Error! password is empty!"
            self.s = Session()
            self.s.headers['User-Agent'] = UA().random()
            self.username = username
            self.userData = copy.deepcopy(userData)
            self.userData["username"] = username
            self.userData["password"] = password
            self.postTime = postTime.replace('，', ',').replace('：', ':').replace(' ', '')
            assert self.postTime, "Error! Invalid time!"
            self.postTime = [self.postTime,] if ',' not in self.postTime else [i for i in self.postTime.split(',') if i]
            self.postTime = list(set(self.postTime))
            self.crypt = Crypt
        except Exception as e:
            error(repr(e))
            print(repr(e))

    def isNeedCaptcha(self) -> bool:
        try:
            urlFormat = "http://authserver.nuist.edu.cn/authserver/checkNeedCaptcha.htl?username={username}&_={timestamp}"
            url = urlFormat.format(username=self.username, timestamp=int(time.time()))
            res = self.s.get(url).json()
            return res['isNeed']
        except Exception as e:
            warn(repr(e))
            return None

    def run(self, retry: int = 3) -> bool:
        try:
            debug("Try to get main page...")
            temp = self.s.get(indexUrl, timeout=15)
            tempBS = bs(temp)
            pwdSalt = [i.get('value') for i in tempBS.findAll('input') if i.has_attr('id') and i.get('id') == 'pwdEncryptSalt'][0]
            execute = [i.get('value') for i in tempBS.findAll('input') if i.has_attr('id') and i.get('id') == 'execution'][0]
            self.userData['password'] = self.crypt(self.userData['password'], pwdSalt)
            self.userData['execution'] = execute
            if temp.status_code != 200:
                error("Get index url failed! status code: {}".format(temp.status_code))
                raise SelfAbort
            debug("Get main page success!")
            debug("Try to know whether need captcha...")
            result = self.isNeedCaptcha()
            if result:
                warn("User({}) need captcha to login!".format(self.username))
            else:
                debug("User({}) don't need captcha to login.".format(self.username))
            temp = self.s.post(loginUrl, data=self.userData)
            if temp.status_code != 200:
                error("Post user data to loginUrl success, but got status code: {}".format(temp.status_code))
                raise SelfAbort
            if 'http://my.nuist.edu.cn/index.portal' == temp.url:
                info("User({}) login success!".format(self.username))
            else:
                error(f"Auto login failed! Return message: {temp.text}")
                raise SelfAbort
            debug('Try to get render url...')
            temp = self.s.get(renderUrl, timeout=15)
            csrfToken = '1' * 32
            if temp.status_code != 200:
                warn("Get render url success but got status code: {}".format(temp.status_code))
            debug('Get render url success!')
            renderData = {
                    'idc': 'XNYQSB',
                    'release': '',
                    'csrfToken': csrfToken,
                    'formData': '{"_VAR_URL":"http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start","_VAR_URL_Attr":"{}"}'
                 }
            debug('Try post data to render url...')
            targetUrl = ''
            startUrl = 'http://e-office2.nuist.edu.cn/infoplus/interface/start'
            self.s.headers['Referer'] = 'http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start'
            temp = self.s.post(startUrl, data=renderData, timeout=15)
            debug('Received data length: {}'.format(len(temp.text)))
            if temp.status_code != 200:
                error("Post render data to startUrl success, but got status code: {}".format(temp.status_code))
                raise SelfAbort
            if temp.json()['errno'] == 10091:
                if temp.json()['entities']:
                    info("Got csrfToken.")
                    csrfToken = temp.json()['entities'][0]
                    renderData['csrfToken'] = csrfToken
                    debug('Try to use csrfToken({}) to post...'.format(csrfToken))
                    temp = self.s.post(startUrl, data=renderData, timeout=15)
                    if temp.status_code != 200:
                        error('Post render data to render url success, but got status code: {}'.format(temp.status_code))
                        raise SelfAbort
                    if temp.json()['errno'] == 0:
                        info('Login success.')
                        targetUrl = temp.json()['entities'][0]
                        debug('Get target Url success!')
                    else:
                        error('Login failed! Received data: {}'.format(temp.json()))
                        raise SelfAbort
                else:
                    error('Post render data to startUrl success, but server did not return the csrfToken.')
                    raise SelfAbort
            elif temp.json()['errno'] == 16005:
                error('Post render data to server success, but server told login session expired.')
                raise SelfAbort
            elif temp.json()['errno'] == 0:
                info('Login success.')
                targetUrl = temp.json()['entities'][0]
                debug('Get target Url success! Received data: {}'.format(temp.json()))
            stepId = targetUrl.split('/')[-2]
            rand = str(random.random() * 1000)
            renderPostData = {
                    'stepId': stepId,
                    'instanceId': '',
                    'admin': False,
                    'rand': rand,
                    'width': '1920',
                    'lang': 'zh',
                    'csrfToken': csrfToken
                }
            recvUrl = "http://e-office2.nuist.edu.cn/infoplus/interface/render"
            temp = self.s.post(recvUrl, data=renderPostData, timeout=15)
            if temp.status_code != 200:
                error('Post render post data to server but got status code: {}'.format(temp.status_code))
                raise SelfAbort
            debug("Received data length: {}".format(len(temp.text)))
            selfData = temp.json()
            if selfData['errno'] == 0:
                info('Got self data success!')
            else:
                error('Failed to get self data!')
                debug('received self data is: {}'.format(selfData))
                raise SelfAbort
            recvData = selfData['entities'][0]['data']
            recvData["_VAR_ENTRY_NAME"] = "学生健康状况申报"
            recvData["_VAR_ENTRY_TAGS"] = "学工部"
            recvData["_VAR_URL"] = targetUrl
            recvData["fieldCNS"] = True
            recvData["fieldCXXXfxxq"] = "1"
            recvData["fieldCXXXfxxq_Name"] = "南京校区"
            recvData["fieldSTQKfrtw"] = str(random.randint(365, 371) / 10).ljust(3, '0')[:4]
            listNextUrl = 'http://e-office2.nuist.edu.cn/infoplus/interface/listNextStepsUsers'
            sendData = {
                    'stepId': stepId,
                    'actionId': '1',
                    'formData': str(recvData),
                    'timestamp': str(time.time()).split('.')[0],
                    'rand': str(random.random() * 1000),
                    'boundFields': 'fieldCXXXjtgjbc,fieldMQJCRxh,fieldCXXXsftjhb,fieldSTQKqt,fieldSTQKglsjrq,fieldYQJLjrsfczbldqzt,fieldCXXXjtfsqtms,fieldCXXXjtfsfj,fieldJBXXjjlxrdh,fieldJBXXxm,fieldJBXXjgsjtdz,fieldSTQKfrtw,fieldMQJCRxm,fieldCXXXsftjhbq,fieldSTQKqtms,fieldCXXXjtfslc,fieldJBXXlxfs,fieldJBXXxb,fieldCXXXjtfspc,fieldYQJLsfjcqtbl,fieldCXXXssh,fieldJBXXgh,fieldCNS,fieldYC,fieldSTQKfl,fieldCXXXsftjwh,fieldCXXXfxxq,fieldSTQKdqstzk,fieldSTQKhxkn,fieldSTQKqtqksm,fieldFLid,fieldYQJLjrsfczbl,fieldJBXXjjlxr,fieldCXXXfxcfsj,fieldMQJCRcjdd,fieldSQSJ,fieldSTQKfrsjrq,fieldSTQKks,fieldJBXXcsny,fieldSTQKgm,fieldJBXXnj,fieldCXXXjtzzq,fieldJBXXJG,fieldCXXXdqszd,fieldCXXXjtzzs,fieldSTQKfx,fieldSTQKfs,fieldCXXXjtfsdb,fieldCXXXcxzt,fieldCXXXjtfshc,fieldCXXXjtjtzz,fieldCXXXsftjhbs,fieldJBXXsfzh,fieldSTQKsfstbs,fieldCXXXcqwdq,fieldJBXXfdygh,fieldJBXXjgshi,fieldJBXXfdyxm,fieldWXTS,fieldCXXXjtzz,fieldJBXXjgq,fieldCXXXjtfsqt,fieldJBXXjgs,fieldSTQKfrsjsf,fieldSTQKglsjsf,fieldJBXXdw,fieldCXXXsftjhbjtdz,fieldMQJCRlxfs',
                    'csrfToken': csrfToken,
                    'lang': 'zh'
                }
            debug('Try to send data to list next step user url with Tempreture: {}℃...'.format(recvData["fieldSTQKfrtw"]))
            temp = self.s.post(listNextUrl, data=sendData, timeout=15)
            if temp.status_code != 200:
                error('Post data failed! Status code is: {}'.format(temp.status_code))
                raise SelfAbort
            if temp.json()['errno'] != 0:
                error('Post data success but got failed data: {}'.format(temp.json()))
                raise SelfAbort
            info('Post the first one finished!')
            doAction = 'http://e-office2.nuist.edu.cn/infoplus/interface/doAction'
            secondData = {
                    'actionId': '1',
                    'formData': str(recvData),
                    'remark': '',
                    'rand': str(random.random() * 1000),
                    'nextUsers': "{}",
                    'stepId': stepId,
                    'timestamp': str(time.time()).split('.')[0],
                    'boundFields': 'fieldCXXXjtgjbc,fieldMQJCRxh,fieldCXXXsftjhb,fieldSTQKqt,fieldSTQKglsjrq,fieldYQJLjrsfczbldqzt,fieldCXXXjtfsqtms,fieldCXXXjtfsfj,fieldJBXXjjlxrdh,fieldJBXXxm,fieldJBXXjgsjtdz,fieldSTQKfrtw,fieldMQJCRxm,fieldCXXXsftjhbq,fieldSTQKqtms,fieldCXXXjtfslc,fieldJBXXlxfs,fieldJBXXxb,fieldCXXXjtfspc,fieldYQJLsfjcqtbl,fieldCXXXssh,fieldJBXXgh,fieldCNS,fieldYC,fieldSTQKfl,fieldCXXXsftjwh,fieldCXXXfxxq,fieldSTQKdqstzk,fieldSTQKhxkn,fieldSTQKqtqksm,fieldFLid,fieldYQJLjrsfczbl,fieldJBXXjjlxr,fieldCXXXfxcfsj,fieldMQJCRcjdd,fieldSQSJ,fieldSTQKfrsjrq,fieldSTQKks,fieldJBXXcsny,fieldSTQKgm,fieldJBXXnj,fieldCXXXjtzzq,fieldJBXXJG,fieldCXXXdqszd,fieldCXXXjtzzs,fieldSTQKfx,fieldSTQKfs,fieldCXXXjtfsdb,fieldCXXXcxzt,fieldCXXXjtfshc,fieldCXXXjtjtzz,fieldCXXXsftjhbs,fieldJBXXsfzh,fieldSTQKsfstbs,fieldCXXXcqwdq,fieldJBXXfdygh,fieldJBXXjgshi,fieldJBXXfdyxm,fieldWXTS,fieldCXXXjtzz,fieldJBXXjgq,fieldCXXXjtfsqt,fieldJBXXjgs,fieldSTQKfrsjsf,fieldSTQKglsjsf,fieldJBXXdw,fieldCXXXsftjhbjtdz,fieldMQJCRlxfs',
                    'csrfToken': csrfToken,
                    'lang': 'zh'
                }
            debug('Try to resend data to do action url...')
            temp = self.s.post(doAction, data=secondData, timeout=15)
            if temp.status_code != 200:
                error('Post data failed! Status code is: {}'.format(temp.status_code))
                raise SelfAbort
            if temp.json()['errno'] != 0:
                error('Post data success but got failed data: {}'.format(temp.json()))
                raise SelfAbort
            info('Post data finished with no error.')
            return True
        except SelfAbort:
            if retry == 0:
                error("Max Retried times!")
                return False
            warn("Retry times: {}".format(3 - retry + 1))
            return self.run(retry - 1)
        except Exception as e:
            warn(repr(e))
            if retry < 0:
                error("Max Retried times!")
                return False
            warn("Retry times: {}".format(3 - retry + 1))
            return self.run(retry - 1)

class UserClass():
    def __init__(self, config: dict) -> None:
        try:
            self.config = config
            self.count = 0
            self.success = 0
            self.failed = 0
            self.username = config['username']
            assert self.username, "Error! Received a config dict without username!"
            self.nickname = config['nickname']
            self.login = AutoLogin(username=config['username'], password=config['password'], postTime=config['postTime'])
            self.postTime = self.login.postTime
            self.runLock = False
            self.lastPostTime = ''
            self.lastPostTimeStamp = 0.0
            self.postTime = [i.zfill(5) for i in self.postTime]
            assert self.postTime, "Error! User({}) don't have postTime info!".format(self.username)
            self.postTime.sort()
            self.timecost = 0
            self.lastResult = ''
            
        except Exception as e:
            error(repr(e))
            print(repr(e))
            exit(0)
    
    def status(self) -> str:
        if self.lastResult:
            return self.lastResult
        else:
            if self.runLock:
                return "Running"
            else:
                return "Waiting"
    
    def getNextTime(self):
        for i in self.postTime:
            if time.strftime("%H:%M", time.localtime()) < i:
                return time.strftime("%Y-%m-%d ", time.localtime()) + i
        return time.strftime("%Y-%m-%d ", time.localtime(time.time() + 60 * 60 * 24)) + self.postTime[0]
    
    def run(self) -> None:
        if self.runLock:
            return None
        self.runLock = True
        debug(f"User({self.username}): Set run lock success.")
        start = time.time()
        result = self.login.run()
        self.timecost = time.time() - start
        self.lastResult = "Success" if result else "Failed"
        self.lastPostTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        debug(f"User({self.username}): " + "Finished. Cost: {:6.3f} s".format(self.timecost))
        if result:
            self.success += 1
        else:
            self.failed += 1
        self.count += 1
        debug(f"User({self.username}): " + "Unset run lock success.")
        self.runLock = False
        return None

def getTime(runTime: float = 0.0) -> str:
    realTime = int(time.time() - runTime)
    day = int(realTime // (60 * 60 * 24))
    realTime %= 60 * 60 * 24
    hour = str(int(realTime) // (60 * 60)).zfill(2)
    realTime %= 60 * 60
    mins = str(int(realTime) // 60).zfill(2)
    realTime %= 60
    secs = str(realTime).zfill(2)
    info = '' if day == 0 else ("1 day " if day == 1 else f"{day} days ")
    info += f'{hour}:{mins}:{secs}'
    return info

def genUserInfo(num: int = 1) -> dict:
    global configFormat
    try:
        tempDict = copy.deepcopy(configFormat)
        print(f" No.{num} ".center(8, '*').ljust(20))
        tempDict['username'] = input("Enter the username: ".ljust(20))
        tempDict['password'] = input("Enter the password: ".ljust(20))
        tempDict['nickname'] = input("Enter the nickname: ".ljust(20))[:20]
        assert tempDict['nickname'].isascii(), "Error! Nickname should be ascii letters! and length should lower than 20!"
        tempDict['postTime'] = input("Enter the postTime: ".ljust(20))
        return tempDict
    except KeyboardInterrupt:
        print('User Abort.')
        return {}
    except Exception as e:
        print(repr(e))
        return {}

def makeConfig():
    global configFile
    try:
        if os.path.isfile(configFile):
            f = open(configFile, "r")
            data = f.read().encode('raw_unicode_escape').decode('utf-8')
            f.close()
            totalConfig = json.loads(data)
        else:
            totalConfig = []
        number = int(input("Enter the number of users:".ljust(20)))
        for i in range(number):
            result = genUserInfo(len(totalConfig) + 1)
            if result:
                totalConfig.append(result)
            else:
                break
        print("config make success.")
        f = open(configFile, "w+")
        data = json.dumps(totalConfig, indent=4, separators=(',',':')).encode('utf-8').decode('raw_unicode_escape')
        f.write(data)
        f.close()
        return None
    except KeyboardInterrupt:
        print("User abort.")
        info("User abort.")
    except Exception as e:
        print(repr(e))
        error(repr(e))

def readConfig() -> list:
    global configFile
    try:
        if os.path.isfile(configFile):
            f = open(configFile, 'r')
            data = json.load(f)
            f.close()
            return data
        else:
            return []
    except Exception as e:
        error(repr(e))
        print("Read config failed: " + repr(e))

def getInfo(x: UserClass):
    infoFormat = "{:15s} {:20s} {:20s} {:8s} {:18s} {:4d} {:4d} {:4d}"
    return infoFormat.format(
            x.username.center(15),
            x.nickname[:20].center(20),
            x.lastPostTime.center(20),
            x.status().center(8),
            x.getNextTime().center(18),
            x.success,
            x.failed,
            x.count
        )

def echoInfo(stdscr):
    global userDataList
    try:
        startTime = time.time()
        infoBar = "{}|{}|{}|{}|{}|{}|{}|{}".format(
                "username".center(15),
                "nickname".center(20),
                "last post time".center(20),
                "status".center(8),
                'next post time'.center(18),
                'OK'.center(4),
                "err".center(4),
                'all'.center(4)
            )
        while True:
            curses.curs_set(False)
            stdscr.clear()
            rows = len(userDataList) + 6 if len(userDataList) > 6 else 15
            curses.resize_term(rows, 100)
            stdscr.addstr(0, 0, "Multi-Post Script Monitor".center(100), curses.A_REVERSE | curses.A_BOLD)
            stdscr.addstr(2, 0, "\b" * 100 + f"Now time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} Running time: {getTime(startTime)}".center(100))
            stdscr.addstr(4, 0, infoBar, curses.A_REVERSE | curses.A_ITALIC)
            for i in range(len(userDataList)):
                stdscr.addstr(i + 5, 0, getInfo(userDataList[i]))
            stdscr.refresh()
            time.sleep(0.5)
    except Exception as e:
        error(repr(e))

def runAll(targetList: list) -> None:
    try:
        for i in targetList:
            i.run()
    except Exception as e:
        error(repr(e))

def timeManager():
    global userDataList
    timeList = []
    last = ''
    for i in userDataList:
        for j in i.postTime:
            timeList.append(j)
    timeList = list(set(timeList))
    timeDict = {i: [] for i in timeList}
    for i in userDataList:
        for j in i.postTime:
            timeDict[j].append(i)
    while True:
        now = time.strftime("%H:%M", time.localtime())
        if now in timeDict.keys() and now != last:
            last = now
            thread = threading.Thread(target=runAll, args=(timeDict[now], ))
            thread.setDaemon(True)
            thread.start()
        time.sleep(0.5)

def main():
    global userDataList, LOG_LIST, defaultLog
    try:
        user("DEBUG", f"Default Log Level: {LOG_LIST[defaultLog]}")
        command = ''
        helpInfo = """wrong input.
please see README.md file."""
        if len(sys.argv) != 2:
            print(helpInfo)
            return None
        else:
            command = sys.argv[1].lower()
        if command == 'config':
            return makeConfig()
        elif command == 'loop':
            configs = readConfig()
            for i in configs:
                userDataList.append(UserClass(i))
            timeManagerThread = threading.Thread(target=timeManager)
            timeManagerThread.setDaemon(True)
            timeManagerThread.start()
            time.sleep(1)
            curses.wrapper(echoInfo)
    except KeyboardInterrupt:
        info("User abort.")
        print('Abort.')
    except Exception as e:
        print(repr(e))
        error(repr(e))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error(repr(e))
        exit(0)
