# 导入所需的模块和类
from wxautox4 import (
    WeChat,  # 微信自动化主类
    Chat     # 聊天窗口类
)
from wxautox4.msgs import (
    BaseMessage  # 基础消息类
)
import typing  # 类型提示支持
from src.components.logger.logger import create  # 日志创建器


# 创建日志记录器
logger = create(__name__)
# 定义消息回调函数的类型别名
message_callback = typing.Callable[[BaseMessage, Chat], None]
class WeChatEvent(WeChat):
    def __init__(self, chat: WeChat):
        self.we_chat = chat

        # 初始化消息事件字典结构
        # 第一层：用户昵称，第二层：事件名，第三层：消息类型
        self._msg_events: dict[str, dict[str, dict[str, list[message_callback]]]] = {}
        # 已监听的用户列表
        self._listed: list[str] = []
        

    def _on_listen_message(self, message: BaseMessage, chat: Chat):
        # 记录接收到的消息信息
        logger.info(f"receved message type: {message.type}, attr: {message.attr}, sender: {message.sender}")
        # 获取特定昵称的事件处理
        nickname_events = self._msg_events.get(chat.who)
        if nickname_events:
            # 获取特定属性的事件处理
            handlers = nickname_events.get(message.attr)
            if handlers:
                # 遍历并执行所有匹配的回调函数
                for callback in handlers.get(message.type, []):
                    callback(message, chat)

        # 获取全局事件处理
        all_type_handlers = self._msg_events.get("all")
        if all_type_handlers:
            event_types = all_type_handlers.get("all")
            if event_types:
                # 遍历并执行所有全局回调函数
                for callback in event_types.get("all", []):
                    callback(message, chat)

        
    def add_listen(self, event_name: str, callback: message_callback):
        """
        订阅消息事件
        Args:
            - event_name: 事件名称 示例: `friend/text,voice:张三`
                - 格式: 消息类型/具体类型:昵称
                - 消息类型: friend(好友), group(群聊)等
                - 具体类型: text(文本), voice(语音), image(图片)等
                - 多个类型用逗号分隔
            - callback: 处理回调函数，接收消息和聊天对象两个参数
        """
        # 解析事件名称
        t = event_name.split(":")
        if len(t) != 2:
            raise ValueError("事件名称格式错误")
        event, nickname = t

        # 解析事件类型
        et = event.split('/')
        if len(et) != 2:
            raise ValueError("事件格式错误")
        event_type, msg_types = et

        # 昵称的事件
        if nickname in self._msg_events:
            nickname_events = self._msg_events[nickname]
            if event_type in nickname_events:
                for msg_type in msg_types.split(","):
                    handlers = nickname_events[event_type].get(msg_type)
                    if handlers:
                        handlers.append(callback)
                    else:
                        nickname_events[event_type][msg_type] = [callback]
            else:
                nickname_events[event_type] = {}
                for msg_type in msg_types.split(","):
                    handlers = nickname_events[event_type].get(msg_type)
                    if handlers:
                        handlers.append(callback)
                    else:
                        nickname_events[event_type][msg_type] = [callback]
        else:
            self._msg_events[nickname] = {event_type: {}}
            for msg_type in msg_types.split(","):
                self._msg_events[nickname][event_type][msg_type] = [callback]

        if nickname not in self._listed:
            self.we_chat.AddListenChat(nickname, self._on_listen_message)
            self._listed.append(nickname)
    
    def remove_listen(self, event_name: str, callback: message_callback | None = None):
        """
        移除订阅的消息事件
        Args:
            - event_name: 指定事件消息名称
            - callback: 要移除的回调函数
        """
        t = event_name.split(":")
        if len(t) == 1 and event_name in self._msg_events: # 直接移除昵称下所有的事件
            self._msg_events.pop(event_name)
            self.we_chat.RemoveListenChat(event_name)   # 移除对话监听
            return
        elif len(t) != 2:
            raise ValueError("事件名称格式错误")
        event, nickname = t

        if nickname not in self._msg_events:
            return
        nickname_events = self._msg_events[nickname]

        et = event.split('/')
        if len(et) == 1 and event in nickname_events:
            nickname_events.pop(event)
            if not nickname_events:
                self.we_chat.RemoveListenChat(event_name)   # 移除对话监听
            return
        elif len(et) != 2:
            raise ValueError("事件格式错误")
        event_type, msg_types = et

        if event_type not in nickname_events:
            return
        type_events = nickname_events[event_type]

        for msg_type in msg_types.split(","):
            if msg_type in type_events:
                if callback:
                    type_events[msg_type].remove(callback)
                    if type_events[msg_type]:
                        type_events.pop(msg_type)
                else:
                    type_events.pop(msg_type)
        
        if not type_events:
            nickname_events.pop(event_type)
        if not nickname_events:
            self._msg_events.pop(nickname)
            self.we_chat.RemoveListenChat(event_name)   # 移除对话监听
