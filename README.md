# Countdown-Bot

#### 项目介绍

QQ群倒计时bot.


#### 安装教程

前置需求:

- Coolq
- Python3.5+
- cqhttp (使用pip安装)
- docker (Python的docker客户端，用pip安装)
- texlive pyglet dvipng (如果需要渲染Latex)

#### 使用说明

- 复制config_default.py为config.py,并作出相应修改
- 使用python运行main.py
- 在群里输入--help查看帮助


#### 注意
- 如果要使用运行Python代码的功能，则系统必须要安装有docker，并且已经安装好了"python"镜像
- 要渲染Latex，则必须安装sympy,pyglet,dvipng,texlive
- 要支持积分，必须安装sympy
- 如果要使用music_gen插件，则必须安装ffmpeg和sox