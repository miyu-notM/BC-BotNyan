## bot喵
是BC聊天室的bot喵~

## 注意喵
代码是miyu边学边写的喵，所以代码结构很差喵，包括以下问题喵：
- 函数、变量命名不清晰喵
- 代码注释混乱喵，有注释掉的测试代码忘了删喵，还有中英文混在一起喵
- 虽然后来重构过，但是还是有硬编码的东西没法删掉喵（比如bot喵的外貌代码就是硬写在BOT_base类里的喵
- 没有配置文件喵（miyu不会写喵
- 可能还有奇怪的bug喵

有什么不满去找miyu喵，怎么教训都不会有意见的喵

## 使用
建议py310以上喵

直接使用:
```
git clone https://github.com/miyu-notM/BC-BotNyan botnyan
cd botnyan
mkdir log
pip install asyncio socketio colorama
pip install "python-socketio[asyncio_client]"
```
记得修改botnyan.py里的用户名密码喵,在main()里喵
然后
```
python botnyan.py
```

## 代码结构
`BOT_base.py` 里的 `BOT` in `BOT_base.py` 是包含了登录、进入聊天室和监听对话的bot喵，但是它什么都不做喵  
`botnyan.py` 的 `BOTNyan`是`BOT`的子类喵，添加了帮忙解绑之类的特殊行动喵，就是咱的说喵


## BC-BotNyan

a bot for an online adult game.

## warning
- bad naming (function, variable,...)
- bad comments  
  - mixture of Chinese & English  
  - mixture of real comments & abandoned code  
  - ...
- bad code structure (it's not OOP from the start)
- hard coded configurations
- may contain bugs
- ...

## usage
```
git clone https://github.com/miyu-notM/BC-BotNyan botnyan
cd botnyan
mkdir log
pip install asyncio socketio colorama
pip install "python-socketio[asyncio_client]"
```

then modify username and passwords in `botnyan.py::main()`
```
python botnyan.py
```
tested on python 3.10

## file description
`BOT` in `BOT_base.py` contains necessary code to login the website, create/join chatrooms and listen to others chats.  
`BOTNyan` in `botnyan.py` is an subclass of `BOT`, which has more capabilities.
