# Countdown-Bot

#### 项目介绍

QQ群多功能Bot。



#### 安装教程

前置需求:

- Coolq + HTTPAPI
- Python3.8
- requires.txt里的各种库

#### 使用说明

- 安装requires.txt里的依赖
- HTTPAPI以HTTP形式上报数据
- 参考common.countdown_bot.CountdownBotConfig类在Bot根目录下写自己的配置文件(config.py，使用全局常量来覆盖默认配置)


#### 注意
- 如果要使用运行Python代码的功能，则系统必须要安装有docker，并且已经安装好了"python"镜像
- 如果要使用music_gen插件，则必须安装ffmpeg和sox
- 插件可以自由删除，删除任何一个插件都不会影响其他插件运行