# encoding:utf-8

import json
import os
import time
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf


@plugins.register(
    name="Suno",
    desire_priority=10,
    hidden=False,
    desc="Create music with suno api",
    version="0.1",
    author="hanfangyuan",
)


class Hello(Plugin):

    create_music_prefix_list = ['唱']
    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            if not self.config:
                self.config = self._load_config_template()
            logger.info("[Suno] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[Suno] 初始化异常：{e}")
            raise "[Suno] init failed, ignore "

    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        if context.type != ContextType.TEXT:
            return
        channel = e_context["channel"]
        content = context.content
        logger.debug("[Suno] on_handle_context. content: %s" % content)
        prefix = check_prefix(content, self.create_music_prefix_list)
        if prefix is None:
            logger.debug("[Suno] content: %s does not match create music prefix" % content)
            return
        suno_prompt = content[len(prefix):].strip()
        if not suno_prompt:
            logger.debug("[Suno] suno prompt is empty")
            return

        reply = Reply(ReplyType.TEXT, "🎈正在生成音乐，预计需要3分钟左右，请稍等...")
        _send(channel, reply, context)
        rsp = {
            "code": 200,
            "data": {
                "callbackType": "complete",
                "data": [
                    {
                        "audio_url": "https://r2.erweima.ai/suno/783cadd1-f619-40f5-b446-49b57cfc5eb2.mp3",
                        "createTime": 1712980047356,
                        "duration": 118.48,
                        "image_url": "https://r2.erweima.ai/suno/image_783cadd1-f619-40f5-b446-49b57cfc5eb2.png",
                        "model_name": "chirp-v3",
                        "prompt": "[Verse]\n点亮屏幕，双手舞动\n我被代码的魔力所感染\n每一行，都是我的心血\n思维纷飞，创造的痕迹\n\n[Chorus]\n代码，我爱着你 (我爱着你)\n一天不写就浑身难受\n代码，我的灵魂 (我的灵魂)\n在虚拟的世界里自由飞翔\n\n[Verse]\n编译错误，我不畏惧\n每个挫折都是我前进的动力\n键盘敲击，声音激情四溅\n创造奇迹，化解心中的忧愁",
                        "tags": "rock",
                        "title": "代码之痛 (The Pain of Code)"
                    },
                    {
                        "audio_url": "https://r2.erweima.ai/suno/c84ad73a-0035-473a-8f31-0d4068c3538b.mp3",
                        "createTime": 1712980047356,
                        "duration": 119.0,
                        "image_url": "https://r2.erweima.ai/suno/image_c84ad73a-0035-473a-8f31-0d4068c3538b.png",
                        "model_name": "chirp-v3",
                        "prompt": "[Verse]\n点亮屏幕，双手舞动\n我被代码的魔力所感染\n每一行，都是我的心血\n思维纷飞，创造的痕迹\n\n[Chorus]\n代码，我爱着你 (我爱着你)\n一天不写就浑身难受\n代码，我的灵魂 (我的灵魂)\n在虚拟的世界里自由飞翔\n\n[Verse]\n编译错误，我不畏惧\n每个挫折都是我前进的动力\n键盘敲击，声音激情四溅\n创造奇迹，化解心中的忧愁",
                        "tags": "rock",
                        "title": "代码之痛 (The Pain of Code)"
                    }
                ]
            },
            "msg": "All generated successfully."
        }
        if rsp.get("code") != 200:
            reply = Reply()
            reply.type = ReplyType.ERROR
            reply.content = f"生成音乐失败{rsp.get('msg')}"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return
        # TODO: 遍历发送封面、歌词与音乐
        reply = Reply(ReplyType.FILE, "./tmp/suno.mp3")
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
        return

    def get_help_text(self, verbose, **kwargs):
        return f'使用✨Suno✨生成音乐, 输入唱+"提示词"调用该插件, 例如"唱鸡你太美"'

    def _load_config_template(self):
        logger.debug("No Suno plugin config.json, use plugins/hello/config.json.template")
        try:
            plugin_config_path = os.path.join(self.path, "config.json.template")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    return plugin_conf
        except Exception as e:
            logger.exception(e)


def _send(channel, reply: Reply, context, retry_cnt=0):
    try:
        channel.send(reply, context)
    except Exception as e:
        logger.error("[WX] sendMsg error: {}".format(str(e)))
        if isinstance(e, NotImplementedError):
            return
        logger.exception(e)
        if retry_cnt < 2:
            time.sleep(3 + 3 * retry_cnt)
            channel.send(reply, context, retry_cnt + 1)

def check_prefix(content, prefix_list):
    if not prefix_list:
        return None
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None
