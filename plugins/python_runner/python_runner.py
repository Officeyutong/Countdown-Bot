from global_vars import registered_commands as commands
from register import command
from util import print_log
from threading import Thread
from cqhttp import CQHttp
import ctypes
import inspect
import os
import re
import tempfile
import time
import docker
import util
import global_vars
config = global_vars.CONFIG[__name__]


def plugin():
    return {
        "author": "officeyutong",
        "version": 1.0,
        "description": "可以在Docker内运行Python代码."
    }


@command(name="exec", help="在Docker中执行Python3.6代码")
def exec_python_code(bot: CQHttp, context=None, args=None):
    def callback(msg):
        bot.send(context, msg)
    code = "".join(map(lambda x: x+" ", args[1:]))
    pattern = re.compile(r'&#(.*?);')
    for item in pattern.findall(code):
        code = code.replace("&#{};".format(
            item), bytes([int(item)]).decode("utf-8"))
    code = f"""CALLER_UID={context['user_id']}\nCALLER_NICKNAME={str(context['sender']['nickname']).encode()}.decode()\nCALLER_CARD={str(context['sender']['card']).encode()}.decode()\n"""+code
    run_python_in_docker(callback, code)


def execute_daemon_calc(callback, container):
    container.start()
    container.reload()
    while container.status == "running":
        container.reload()
        import time
        time.sleep(0.1)
    output = container.logs().decode("UTF-8")
    container.remove()
    if len(output) > config.OUTPUT_LENGTH_LIMIT:
        output = output[:config.OUTPUT_LENGTH_LIMIT]+"[超出长度限制部分已截断]"
    callback(output)
    # print("{} = {}".format(expression, output))


def keeper_thread(thread, callback,  container, code):
    time.sleep(config.EXECUTE_TIME_LIMIT/1000)
    try:
        container.reload()
    except Exception as ex:
        print_log(ex)
        return
    print_log("Waiting timed out , status = {}".format(container.status))
    if container.status == "running":
        util.stop_thread(thread)
        try:
            container.kill()
            container.remove()
        except Exception:
            pass
        callback("代码 '"+code+"' 执行超时.")
        print_log("Killing")


def run_python_in_docker(callback, code):
    print_log("Running .. '{}'".format(code))
    client = docker.from_env()
    # client = docker.DockerClient(base_url="tcp://192.168.10.134:2375")
    tmp_dir = tempfile.mkdtemp()
    file_name = "temp.py"
    with open(os.path.join(tmp_dir, file_name), "w") as file:
        file.write("{}".format(code))
    print_log("Container created.")
    container = client.containers.create(config.DOCKER_IMAGE, "python /temp/{}".format(
        file_name), tty=True, detach=False, network_mode="none",  volumes={tmp_dir: {"bind": "/temp", "mode": "ro"}}, mem_limit="50m", memswap_limit="50m", oom_kill_disable=True, nano_cpus=int(0.1*1/1e-9))
    # container = client.containers.create("python", "uname -a".format(
    #     file_name), tty=True, detach=False)
    thd = Thread(target=execute_daemon_calc, args=(
        callback, container))
    thd.setDaemon(True)
    thd.start()
    keeper = Thread(target=keeper_thread, args=(
        thd, callback, container, code))
    keeper.setDaemon(True)
    keeper.start()
