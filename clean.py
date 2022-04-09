import os
import time
import datetime
log_name=time.strftime("%Y-%m-%d")
log_name="./log/"+log_name.replace("-","_")+".txt"
f = open(str(log_name),mode="a")
try:
    os.remove("fail.json")
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    f.write(now_time + " ok文件删除成功\n")
except:
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    f.write(now_time+" fail文件不存在，跳过\n")

try:
    os.remove("ok")
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    f.write(now_time+" ok文件删除成功\n")
except:
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    f.write(now_time+" ok文件不存在，跳过\n")


