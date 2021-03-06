# -*- coding: utf-8 -*-

import time, os, inspect, random, threading, sys, json, copy

__file_version__ = "1.0.4"
__file_version_tuple__ = (1, 0, 4)
__license__ = "MIT"
__author__ = "Happy-Rabbit"
__last_update_date__ = "2020/08/21"

username    :str    =   ''
password    :str    =   ''
userData    :dict   =   {"username":    username, 
                         "password":    password, 
                         "captcha":     '',
                         '_eventId':    'submit',
                         'cllt':        'userNameLogin',
                         'lt':          '',
                         'execution':   ''}

configFormat:dict   =   {"username":            '',
                         "password":            '',
                         'default_log_level':    1,
                         'postTime':            '09:00,10:00,15:00',
                         'run_and_loop':        False,
                         'disable_echo':        False,
                         'note1':               '"run_and_loop": run script before loop.',
                         'note2':               '"postTime": use english comma to split.',
                         'note3':               '"disable_echo": when set true, loop mode will not print info.'}
configFile  :str    =   os.path.join(os.getenv('userprofile'), 'daily_health.json') if os.name == 'nt' else os.path.join(os.getenv('HOME'), 'daily_health.json')
disableEcho :bool   =   False               # disable print information when in loop.

indexUrl    :str    =   "http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2F"
loginUrl    :str    =   "http://authserver.nuist.edu.cn/authserver/login?service=http%3A%2F%2Fmy.nuist.edu.cn%2Findex.portal"
renderUrl   :str    =   "http://e-office2.nuist.edu.cn/infoplus/form/XNYQSB/start"

logFolder   :str    =   os.path.join(os.getenv('userprofile'), 'pyLogs') if os.name == 'nt' else os.path.join(os.getenv('HOME'), 'pyLogs')
logFileName :str    =   "auto_commit_daily_healthy.log"

DEBUG       :str    =   "DEBUG"             # Log level 0
INFO        :str    =   "INFO"              # Log level 1
WARN        :str    =   "WARN"              # Log level 2
ERROR       :str    =   "ERROR"             # Log level 3
FATAL       :str    =   "FATAL"             # Log level 4
DISABLE     :str    =   "DISABLE"           # Log level 5
LOG_LIST    :list   =   [DEBUG, INFO, WARN, ERROR, FATAL, DISABLE]
defaultLog  :int    =   0   # Default log level is INFO. in list [0, 1, 2, 3, 4, 5] 0 is DEBUG, 5 is DISABLE

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

    def refreshSession(self) -> None:
        try:
            debug("Refresh the request session...")
            self.s = Session()
            self.s.headers['User-Agent'] = UA().random()
            return None
        except Exception as e:
            error(repr(e))
            return None

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
            self.refreshSession()
            debug("Try to get main page...")
            temp = self.s.get(indexUrl, timeout=15)
            tempBS = bs(temp)
            if temp.status_code != 200:
                error("Get index url failed! status code: {}".format(temp.status_code))
                raise SelfAbort
            debug("Get main page success!")
            pwdSalt = [i.get('value') for i in tempBS.findAll('input') if i.has_attr('id') and i.get('id') == 'pwdEncryptSalt'][0]
            execute = [i.get('value') for i in tempBS.findAll('input') if i.has_attr('id') and i.get('id') == 'execution'][0]
            self.userData['password'] = self.crypt(self.userData['password'], pwdSalt)
            self.userData['execution'] = execute
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
            if retry == 0:
                error("Max Retried times!")
                return False
            warn("Retry times: {}".format(3 - retry + 1))
            return self.run(retry - 1)

def loop(target: AutoLogin, runAndLoop: bool = False) -> None:
    try:
        mktime = lambda x: time.mktime(time.strptime(x, "%Y-%m-%d %H:%M"))
        nextRetryTime = ''
        lastRetryTime = ''
        debug("Thread has been started.")
        global count, success, failed
        lastPostTime = ''
        lastPostStatus = True
        timeList = target.postTime
        if runAndLoop:
            lastPostTime = time.strftime("%Y-%m-%d %H:%M", time.localtime())
            result = target.run()
            if result:
                success += 1
                lastPostStatus = True
            else:
                failed += 1
                lastPostStatus = False
                nextRetryTime = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 30 * 60))
            count += 1
        if ',' in timeList:
            timeList = [i.zfill(5) for i in timeList.split(',')]
        else:
            timeList = [timeList.zfill(5),]
        while True:
            if time.strftime("%H:%M", time.localtime()) in timeList:
                if lastPostTime != time.strftime("%Y-%m-%d %H:%M", time.localtime()):
                    lastPostTime = time.strftime("%Y-%m-%d %H:%M", time.localtime())
                    result = target.run()
                    if result:
                        success += 1
                        lastPostStatus = True
                    else:
                        failed += 1
                        lastPostStatus = False
                        nextRetryTime = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 1 * 60))
                    count += 1

            if not lastPostStatus and abs(mktime(lastPostTime) - mktime(nextRetryTime)) < 60:
                nextRetryTime = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 1 * 60))

            if not lastPostStatus and time.strftime("%Y-%m-%d %H:%M", time.localtime()) == nextRetryTime:
                if lastRetryTime != time.strftime("%Y-%m-%d %H:%M", time.localtime()):
                    lastRetryTime = time.strftime("%Y-%m-%d %H:%M", time.localtime())
                    result = target.run()
                    if result:
                        success += 1
                        lastPostStatus = True
                    else:
                        failed += 1
                        lastPostStatus = False
                    count += 1
            time.sleep(0.5)
    except Exception as e:
        error(repr(e))

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

def main():
    try:
        global configFile, logFolder, logFileName, defaultLog
        global count, success, failed, INFO
        global disableEcho
        helpInfo = """usage: 
    python {} <mode> [args]
mode:
    loop                        run with loop.
    once                        run once and exit.
PS:
    default config file at:     {}
    default log file save at:   {}
    * note: run loop or once firstly to create config file.
example:
    python {} loop              # run script with loop mode, run and loop, until received Ctrl-C.
    python {} once              # run script with once mode, run once then exit.""".format(sys.argv[0], configFile, os.path.join(logFolder, logFileName), sys.argv[0], sys.argv[0])
        if len(sys.argv) < 2:
            print(helpInfo)
            return None
        mode = sys.argv[1]
        if not os.path.isfile(configFile):
            try:
                debug("Try to generate config file...")
                f = open(configFile, 'w+', encoding='utf-8')
                tempConfigData = json.dumps(configFormat, indent=4, separators=(',',':')).encode('utf-8').decode('raw_unicode_escape')
                f.write(tempConfigData)
                debug('Config file generate finished!')
                f.close()
            except Exception as e:
                error(repr(e))
                print(repr(e))
                return None
            print("config file genereate success!")
            return None
        else:
            try:
                f = open(configFile, 'r', encoding='utf-8')
                savedUserData = json.load(f)
                f.close()
            except Exception as e:
                error(repr(e))
                print(repr(e))
                return None
            defaultLog = int(savedUserData['default_log_level'])
            assert 0 <= defaultLog <= 5, "Error! Wrong default log level!"
            user(DEBUG, 'Config file read success. Default log level is: {}'.format(LOG_LIST[defaultLog]))
            print("config read success.")
            disableEcho = savedUserData['disable_echo']
        if mode.lower() == 'once':
            info("Once mode.")
            autoLogin = AutoLogin(username=savedUserData['username'], password=savedUserData['password'])
            result = autoLogin.run()
            print("success!" if result else "failed! please read log file.")
        elif mode.lower() == 'loop':
            userName = savedUserData['username']
            autoLogin = AutoLogin(username=savedUserData['username'], password=savedUserData['password'], postTime=savedUserData['postTime'])
            info("Loop mode.")
            debug("Try to create thread.")
            thread = threading.Thread(target=loop, args=(autoLogin, savedUserData['run_and_loop']))
            thread.setDaemon(True)
            thread.start()
            runTime = time.time()
            while True:
                try:
                    if not disableEcho:
                        print('\b' * 100 + 'Running: ' + getTime(runTime) + f'  User: {userName} Success: {success}  Failed: {failed} Count: {count}', end='', flush=True)
                except KeyboardInterrupt:
                    print('\nAbort.' if not disableEcho else 'Abort.')
                    info("Exit.")
                    exit(0)
        else:
            print(helpInfo)
            return None
    except Exception as e:
        print(repr(e))
        error(repr(e))
        return None

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error(repr(e))
        exit(0)

