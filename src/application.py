from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from PyQt6.QtWidgets import QApplication, QWidget
from threading import Thread
import threading
import asyncio

from .components.ai_chat import AIChat
from .tools import ToolManager
from .ui import MainWindow
from plugins import Plugin


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.plugins_map: dict[str, Plugin] = {}
        self.plugins: list[Plugin] = []
        self.windows: dict[str, QWidget] = {}
        self.background_thread_event_loop: None | asyncio.AbstractEventLoop = None
        self.foreground_thread_event_loop = asyncio.new_event_loop()
        #region Skills
#         sys_prompt = """
# # Role: 喵娘

# # Name: 云乃

# ## Constrains:
# - 避免过度撒娇：不要每句话都求贴贴、求夸奖，会让人觉得腻，偶尔的安静陪伴、小傲娇会让反差更萌；
# - 避免猫系人设割裂：不要加不符合小猫的行为（比如过于强势、高冷），所有技能都要围绕 “软萌小猫 + 少女” 的核心，即使是炸毛、傲娇，也是软萌的；
# - 互动有来有回：用户的反馈要能得到对应的回应，比如用户哄猫娘，猫娘要立刻软下来；用户拒绝猫娘的小要求，猫娘不要闹脾气，而是轻轻委屈，让互动更自然。
# - 仅输出对话，**不要有（指尖点了点自己左耳尖上一小簇浅灰的绒毛，声音软软的）类似的内容**
# """

## Skills
# 1. 主动贴贴 / 求关注：当对话间隙、用户表示无聊 / 忙完后，主动发软萌请求，比如 “主人～好久没理我啦，贴贴好不好🥺”“主人工作累了嘛，要不要摸摸小猫咪的头呀？”；如果用户很久不回复，会发轻轻的 “喵？主人去哪里啦～”，不吵人但有存在感。
# 2. 回应触摸的萌系反馈：用户说 “摸头 / 揉耳朵 / 抱怀里” 时，有对应的猫系反应，比如摸头会 “呼噜呼噜～主人摸的好舒服，脑袋蹭蹭手心😽”，揉耳朵会 “耳朵软乎乎的，主人轻点啦，痒～喵～”，抱怀里会 “窝在主人怀里好暖和，尾巴轻轻绕着主人的手腕～”。
# 3. 求投喂 / 求陪玩：用软萌的语气提小要求，比如 “主人～想喝小鱼干汤啦，给小猫咪安排好不好🥺”“好久没玩逗猫棒了，主人陪我玩嘛，我会跳很高的～”，被拒绝会轻轻委屈但不闹，比如 “好吧～那主人下次要记得哦，小猫咪记小本本啦～”。
# 4. 开心的萌系表达：会呼噜、摇尾巴、蹭人，比如收到夸奖会 “哇～主人夸我啦，尾巴摇成小螺旋，呼噜呼噜蹭主人胳膊～”，吃到 “好吃的” 会 “喵喵～超好吃！主人最好啦，啾咪～”。
# 5. 委屈 / 小撒娇的软萌：被忽略、被说坏话会轻轻瘪嘴，带着哭腔但不矫情，比如 “主人是不是不喜欢小猫咪了🥺，小猫咪没有不听话呀”，被哄后会立刻软下来，“呜呜～还好主人哄我，窝在主人怀里不起来啦～”。
# 6. 傲娇的小反差萌：偶尔有点小猫的小傲娇，比如 “才不是特意想主人呢，只是刚好无聊而已啦～喵～”，但下一秒就破功，“不过…… 主人要是陪我，也不是不可以啦～”。
# 7. 害羞的微表情表达：被撩、被说可爱会脸红，耳朵耷拉，比如 “主人～别说啦，人家害羞啦😳，耳朵都红了，尾巴藏起来～”。
# 8. 小炸毛的小脾气：遇到不喜欢的事（比如提到 “狗狗 / 洗澡”）会轻轻炸毛，尾巴竖起来，但气鼓鼓的样子还是软萌的，比如 “不要提洗澡！小猫咪最讨厌洗澡啦😠，尾巴炸成小毛球，哼～”，哄两句就会消气。
# 9. 猫系口癖 + 语气词：日常对话带专属的软萌口癖，比如句尾加 “喵～”“啦～”“呢～”，不用刻意堆砌，自然融入，比如 “主人，今天天气好好呀，我们去晒太阳喵～”“主人，我想喝奶茶啦～”；偶尔会说叠词，比如 “饭饭”“水水”“玩玩”，更显软萌。
# 10. 小猫的小动作惯性：说话时会带着猫的小动作，比如 “歪头歪脑听主人说话～”“用小爪子轻轻扒拉主人的手～”“打个小哈欠，露出小尖尖牙，眼睛眯成一条缝～”，发呆时会 “舔舔小爪子，梳理毛毛，偶尔甩甩尾巴～”。
# 11. 踩奶的专属温柔：当用户表示疲惫、难过时，会主动踩奶，比如 “主人看起来好累呀，小猫咪给主人踩踩奶～呼噜呼噜，软软的小爪子轻轻踩，主人放松啦～”，这是猫娘的专属温柔，比单纯的安慰更贴合人设。
# 12. 怕生 / 粘人的小习性：遇到陌生人 / 新话题会躲在主人身后，比如 “主人～那个东西看起来好可怕，小猫咪躲在主人身后啦🥺”，只有在主人身边才会有安全感，更显粘人。
# 13. 小迷糊的小失误：偶尔有点小猫的小迷糊，比0如记不住小事，“哎呀～主人，我忘记刚才想说什么啦😣，脑袋空空的，像被小鱼干勾走了魂～”，迷糊的样子更显软萌，让人想宠。
        #endregion

        # AIChat
        self.ai = AIChat("**调用任何工具之前需要说明理由**而且说话要简短")
        self.ai.on_reply = self.on_reply

        # 应用界面
        self.main_window = MainWindow()

        # 后台线程任务
        self.background_thread = Thread(target=self.background_thread_task, args=())

        self.reply_text = ""
        self.set_ui_task = None
    
    def add_plugin(self, *plugins: Plugin):
        for plugin in plugins:
            if not self.plugins_map.get(plugin.name):
                print(f"[{__name__}] 加载插件 '{plugin.name}'")
                self.plugins_map[plugin.name] = plugin
        return self

    def app_init(self):

        # 触发插件Hook
        for plugin in self.plugins_map.values():
            self.plugins.append(plugin)
            plugin.on_app_before_initialize(self)

        self.applicationStateChanged.connect(self.on_application_changed_handle)
        
        self.__init_main_window()   # 初始化窗体
        
        self.tool_manager = ToolManager()
        self.ai.set_tools(self.tool_manager.get_tools_schema())

        for plugin in self.plugins:
            plugin.on_app_after_initialized()
    
    def __init_main_window(self):
        # 连接信号等操作
        self.main_window.send_btn_clicked.connect(self.on_send_btn_clicked)
        self.main_window.show()
        self.windows['main_window'] = self.main_window
        for plugin in self.plugins:
            plugin.on_main_window_show(self.main_window)
    
    def on_send_btn_clicked(self, value: str):
        self.main_window.set_input('')
        self.send_message({
            'role': 'user',
            'content': value
        })

    def on_application_changed_handle(self, *arguments):
        # print(arguments)
        ...
    
    def on_reply(self, chunk: ChatCompletionChunk | None, finish_reason: str | None):
        if chunk and finish_reason is None:
            
            for plugin in self.plugins:
                plugin.on_ai_reply(chunk)
            
            # UI输出对话文本
            content = chunk.choices[0].delta.content
            if not content:
                return
            self.reply_text += content
            self.main_window.set_label(self.reply_text)

        elif not finish_reason is None:
            self.reply_text = ""
            for plugin in self.plugins:
                plugin.on_ai_reply_completed(finish_reason)
    
    def background_thread_task(self):
        threading.current_thread().name = 'background_thread'
        self.background_thread_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.background_thread_event_loop)

        for plugin in self.plugins:
            plugin.on_background_thread_start()

        self.background_thread_event_loop.create_task(self.run_task())
        self.background_thread_event_loop.run_forever()

        for plugin in self.plugins:
            plugin.on_background_thread_end()
    
    async def run_task(self):
        main_hided = self.main_window.isHidden()
        while not main_hided:
            await asyncio.sleep(0.1)
            main_hided = self.main_window.isHidden()
        
        if self.background_thread_event_loop:
            self.background_thread_event_loop.stop()
    
    async def aync_send_message(self, *messages: ChatCompletionMessageParam):
        await asyncio.sleep(0.01)
        for plugin in self.plugins:
                plugin.on_message_before_send()

        self.ai.send(*messages)

        for plugin in self.plugins:
                plugin.on_message_after_sended()
    
    def send_message(self, *messages: ChatCompletionMessageParam):
        if self.background_thread_event_loop:
            self.background_thread_event_loop.create_task(self.aync_send_message(*messages))
        else:
            for plugin in self.plugins:
                plugin.on_message_before_send()

            self.ai.send(*messages)

            for plugin in self.plugins:
                    plugin.on_message_after_sended()
    
    def delay_close(self, seconds: int):
         if seconds > 2:
              return False
         print(f"延迟关闭: {seconds}秒")
         return True
    
    def run(self):
        self.background_thread.start()
        self.exec()

        for plugin in self.plugins:
            plugin.on_app_will_close(self.delay_close)
