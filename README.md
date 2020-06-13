# Countdown-Bot

#### 项目介绍

QQ群多功能Bot。

**项目已经更改架构，旧项目地址https://gitee.com/yutong_java/CountdownBot-Old**


#### 安装教程

前置需求:

- Coolq + HTTPAPI
- Python3.8
- requires.txt里的各种库

#### 使用说明

- 安装requires.txt里的依赖
- **注意:** 此Bot所需要的依赖之一(PySynth)并未在PyPi中提供，但是plugins_new/music_gen/PySynth目录下提供了副本，可以使用```py setup.py install```手动安装
- HTTPAPI以HTTP形式上报数据
- 参考common.countdown_bot.CountdownBotConfig类在Bot根目录下写自己的配置文件(config.py，使用全局常量来覆盖默认配置)


#### 注意
- 如果要使用运行Python代码的功能，则系统必须要安装有docker，并且已经安装好了"python"镜像
- 如果要使用music_gen插件，则必须安装ffmpeg和sox
- 插件可以自由删除，删除任何一个插件都不会影响其他插件运行
- plugins_new目录下，以```_```开头的文件为旧版本留存，可随时删除。
- Bot用到了ujson以提高解析json的速率，但ujson安装时需要调用相应的相应的构建工具(通常在Windows下为MSVC)进行构建，如果您的操作系统下并未安装相应的构建工具，可对Bot所有的源码进行修改，把```ujson```替换为```json```以正常工作。
#### 关于配置文件
- 插件如果使用CountdownBot的配置文件系统，则应该提供一个配置类，用户可以在插件目录下新建自己的config.py文件，并通过其中的全局常量覆盖默认配置中的值

### TODO（预计咕到高考后了）
- 权限系统
- 动态添加监听器

### 其他

如果你觉得此项目不错，欢迎对我进行捐助

![](images/alipay.jpg)