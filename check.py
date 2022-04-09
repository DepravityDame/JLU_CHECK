import json
import time
import requests
import re
import urllib3
import smtplib
import sys
import os
from email.mime.text import MIMEText
import datetime

global fail_list
fail_list = []
urllib3.disable_warnings()  # 关闭https警告

# 定义请求头
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/96.0.4664.45 Safari/537.36"
}


# fiddler代理用
# proxies = {
#     'http': 'http://localhost:8888',
#     'https': 'http://localhost:8888'
# }

# 日志打印函数
def log_print(content):
    now_time = datetime.datetime.now().strftime("%H:%M:%S")  # 获取时间戳
    log_file.write(now_time + content)  # 写入日志文件


# 登录函数
def login_system(s_origin, user):  # 登录过程，获取cookie
    # 访问登录页获取pid
    login_page = s_origin.get("https://ehall.jlu.edu.cn/sso/login/", verify=False)
    data = {
        "username": user["username"],
        "password": user["password"],
        "source": "",
        "pid": ""
    }
    dd = {'pid': re.search(r'.*?name="pid" value="(?P<pid>.*?)"', login_page.text).group('pid')}
    data.update(dd)  # 组合数据体
    log_res = s_origin.post("https://ehall.jlu.edu.cn/sso/login", headers=header, data=data, verify=False)  # 请求登录
    print("登录过程完成")


def check(s_check, user):
    print("打卡过程开始")
    try:  # 避免因账号密码错误导致程序崩溃
        dk_cont = s_check.get("https://ehall.jlu.edu.cn/infoplus/form/YJSMRDK/start", headers=header)  # get获取打卡启动页面
        csrf_token = re.search(r'"csrfToken" content="(?P<csrf>.*?)"', dk_cont.text).group('csrf')  # 获取csrf_token
        data = {
            "idc": "YJSMRDK",
            "release": "",
            "csrfToken": csrf_token,
            "formData": '{"_VAR_URL": "https://ehall.jlu.edu.cn/infoplus/form/YJSMRDK/start", "_VAR_URL_Attr": "{}"}'
        }  # 构建参数数组
        get_from_page = s_check.post("https://ehall.jlu.edu.cn/infoplus/interface/start", data=data)  # 获取目的打卡表单
        print(get_from_page.text)
    except:
        state = 0
        err_content = "用户名或密码错误"
        state_check(state, err_content, user)
        return
    try:#提取打卡表单
        dk_form_url = get_from_page.json()['entities'][0]  # 提取返回的打卡表单
        stepId = re.search(r'/form/(?P<id>.*?)/render', dk_form_url, re.S).group('id')
        # dk_form_page = s_check.get(dk_form_url[0], headers=header)
        dk_data_acquire = {  # post数据部分
            "stepId": stepId,
            "instanceId": "",
            "admin": "false",
            "csrfToken": csrf_token,
        }
        header1 = {"Referer": f"https://ehall.jlu.edu.cn/infoplus/form/{stepId}/render"}  # 构建Referer参数
        get_dk_data = s_check.post("https://ehall.jlu.edu.cn/infoplus/interface/render", headers=header1,
                                   data=dk_data_acquire)  # 获取基础数据
        form_data = get_dk_data.json()["entities"][0]['data']  # 获取数据
        data = {  # 组装提交打卡数据体
            "actionId": "1",
            "formData": json.dumps(form_data),
            "csrfToken": csrf_token,
            "stepId": stepId,
            "nextUsers": "{}",
            "lang": "zh",
            "remark:": "",
            "timestamp": int(time.time())
        }
        check_res = s_check.post("https://ehall.jlu.edu.cn/infoplus/interface/doAction", headers=header1,
                                 data=data)  # 打卡
        state = check_res.json()['ecode']
    except:
        state = 0
        err_content = "csrf错误"
        state_check(state, err_content, user)
        return
    state_check(state, "", user)


def state_check(state, err_content, user):
    if state:
        print(user['username'] + " 打卡成功")
        log_print(user['username'] + " 打卡成功\n")#输出日志
        send_mail(user['email'], user['username'] + " success")#发送成功邮件
    else:
        log_print(user['username'] + " 打卡失败\n")
        print(user['username'] + " 打卡失败")
        global fail_list
        fail_list.append(user)#添加用户到失败列表中
        send_mail(user['email'], "!!!!!!!!!!" + user['username'] + " fail" + "原因是 " + err_content)#发送失败邮件

#邮件发送函数
def send_mail(email, content):
    mail_host = 'smtp.163.com'  # SMTP服务器
    mail_user = '********@163.com'  # 用户名
    mail_pass = "************"  # 密码
    sender = '********@163.com'  # 发件人邮箱(最好写全, 不然会失败)
    title = '打卡状态通知  ' + content  # 邮件主题
    message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
    message['From'] = "{}".format(sender)
    message['To'] = email
    message['Subject'] = title

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
        smtpObj.login(mail_user, mail_pass)  # 登录验证
        smtpObj.sendmail(sender, email, message.as_string())  # 发送
        print("mail has been send successfully.")
    except smtplib.SMTPException as e:
        print(e)

#主函数
if __name__ == "__main__":
    #获取年月日
    log_name = time.strftime("%Y-%m-%d")
    log_name = "./log/" + log_name.replace("-", "_") + ".txt"
    log_file = open(str(log_name), mode="a")
    #初始化state
    state = 777
    try:
        with open("ok", mode="r") as f:
            state = f.read()
    except:
        log_print(" 打卡成功文件不存在，开始打卡\n")
    if state == 'ok':
        log_print(" 已打卡,程序退出\n")
        sys.exit(3)
    # 读取打卡失败人员数据
    # 尝试读取打卡失败列表，若失败列表存在，则不读取打卡成功列表
    try:
        with open("fail.json", mode="r") as f:
            log_print(" 打卡失败列表存在，读取打卡失败列表\n")
            json_date = f.read()
    except:
        with open("dk.json", mode="r") as f:
            log_print(" 读取打卡全员列表\n")
            json_date = f.read()
    users = json.loads(json_date)

    # 读取打卡人员数据

    # 遍历用户打卡
    for user in users:
        s = requests.Session()  # 创建会话
        login_system(s, user)
        check(s, user)
        s.close()  # 关闭进程
    if (len(fail_list) == 0):
        log_print(" 打卡全部成功\n")
        with open("ok", "w") as f:
            f.write("ok")
        log_print(" 删除fail文件\n")
        os.remove("fail.json")
    else:
        log_print(" 打卡部分成功,打卡失败用户存档\n")
        with open("fail.json", mode="w") as f:
            f.write(json.dumps(fail_list))
