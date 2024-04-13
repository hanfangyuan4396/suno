# encoding:utf-8
import json
import os
import threading
from pathlib import Path
from typing import List, Dict

import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *

@plugins.register(
    name="Suno",
    desire_priority=10,
    hidden=False,
    desc="Create music with suno api",
    version="0.1",
    author="hanfangyuan",
)
class Suno(Plugin):

    create_music_prefix_list = ['唱']
    suno_file_root_dir = 'tmp/suno'

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
        try:
            context = e_context["context"]
            if context.type != ContextType.TEXT:
                return
            channel = e_context["channel"]
            content = context.content
            logger.debug("[Suno] on_handle_context. content: %s" % content)
            prefix = self._check_prefix(content, self.create_music_prefix_list)
            if prefix is None:
                logger.debug("[Suno] content: %s does not match create music prefix" % content)
                return
            suno_prompt = content[len(prefix):].strip()
            if not suno_prompt:
                logger.debug("[Suno] suno prompt is empty")
                return

            reply = Reply(ReplyType.TEXT, "🎈正在生成音乐，预计需要3分钟左右，请稍等...")
            channel.send(reply, context)

            base_url = self._get_api_base_url()
            headers = self._get_headers()
            payload = self._get_payload(suno_prompt)
            generate_music_url = f"{base_url}/suno/generate"
            # {
            #     "code": 200,
            #     "data": {
            #         "callbackType": "complete",
            #         "data": [
            #             {
            #                 "audio_url": "https://xxx/suno/783cadd1-f619-40f5-b446-49b57cfc5eb2.mp3",
            #                 "createTime": 1712980047356,
            #                 "duration": 118.48,
            #                 "image_url": "https://xxx/suno/image_783cadd1-f619-40f5-b446-49b57cfc5eb2.png",
            #                 "model_name": "chirp-v3",
            #                 "prompt": "[Verse]\n点亮屏幕，双手舞动\n我被代码的魔力所感染\n每一行，都是我的心血\n思维纷飞，创造的痕迹\n\n[Chorus]\n代码，我爱着你 (我爱着你)\n一天不写就浑身难受\n代码，我的灵魂 (我的灵魂)\n在虚拟的世界里自由飞翔\n\n[Verse]\n编译错误，我不畏惧\n每个挫折都是我前进的动力\n键盘敲击，声音激情四溅\n创造奇迹，化解心中的忧愁",
            #                 "tags": "rock",
            #                 "title": "代码之痛 (The Pain of Code)"
            #             }
            #         ]
            #     },
            #     "msg": "All generated successfully."
            # }
            response = requests.post(generate_music_url, headers=headers, json=payload, timeout=500)
            response.raise_for_status()

            json_response = response.json()
            if json_response.get("code") != 200:
                raise Exception(json_response.get('msg'))

            musics = json_response['data']['data']
            threading.Thread(target=self._prepare_and_send, args=(channel, context, musics)).start()
            reply = Reply(ReplyType.TEXT, "🎉音乐生成完成，请注意查收!")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

        except Exception as e:
            logger.exception(f"[Suno] {str(e)}")
            reply = Reply(ReplyType.ERROR, "我暂时无法生成音乐，请稍后再试")
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

    def _check_prefix(self, content, prefix_list):
        if not prefix_list:
            return None
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None

    def _prepare_and_send(self, channel, context, musics: List[Dict]):
        # [
        #     {
        #         "audio_url": "https://xxx/suno/783cadd1-f619-40f5-b446-49b57cfc5eb2.mp3",
        #         "createTime": 1712980047356,
        #         "duration": 118.48,
        #         "image_url": "https://xxx/suno/image_783cadd1-f619-40f5-b446-49b57cfc5eb2.png",
        #         "model_name": "chirp-v3",
        #         "prompt": "[Verse]\n点亮屏幕，双手舞动\n我被代码的魔力所感染\n每一行，都是我的心血\n思维纷飞，创造的痕迹\n\n[Chorus]\n代码，我爱着你 (我爱着你)\n一天不写就浑身难受\n代码，我的灵魂 (我的灵魂)\n在虚拟的世界里自由飞翔\n\n[Verse]\n编译错误，我不畏惧\n每个挫折都是我前进的动力\n键盘敲击，声音激情四溅\n创造奇迹，化解心中的忧愁",
        #         "tags": "rock",
        #         "title": "代码之痛 (The Pain of Code)"
        #     }
        # ]
        for music in musics:
            # 生成歌词等信息
            title = music['title']
            prompt = music['prompt']
            tags = music['tags']
            model_name = music['model_name']
            
            message = f" 🎸{title}🎸\n{prompt}\n🎧风格: {tags}\n📻模型: {model_name}\n\n-----\n音乐由✨Suno✨生成"
            reply = Reply(ReplyType.TEXT, message)
            channel.send(reply, context)
            # 下载音乐
            audio_path, audio_error = self._download_url(music['audio_url'], title)
            if audio_error:
                logger.error(f'[Suno] 下载音乐失败: {audio_error}')
                return
            reply = Reply(ReplyType.FILE, audio_path)
            channel.send(reply, context)
            # 下载封面图片
            image_url = music['image_url']
            reply = Reply(ReplyType.IMAGE_URL, image_url)
            channel.send(reply, context)

    def _download_url(self, url, file_name):
        try:
            # 确保根目录存在
            root_dir = self.suno_file_root_dir
            Path(root_dir).mkdir(parents=True, exist_ok=True)
            
            # 从URL中提取文件名并获取最后10个字符
            original_file_name = url.split('/')[-1]
            suffix = original_file_name[-10:]  # 获取最后10个字符
            
            # 构建新的文件名
            new_file_name = f"{file_name}_{suffix}"
            file_path = Path(root_dir) / new_file_name
            
            # 下载文件
            response = requests.get(url)
            response.raise_for_status()  # 确保请求成功
            
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return str(file_path), ""
        except Exception as e:
            return "", str(e)

    def _get_api_base_url(self):
        return self.config.get("suno_api_base", "")

    def _get_headers(self):
        return {
            'Authorization': f"Bearer {self.config.get('suno_api_key', '')}"
        }

    def _get_payload(self, prompt):
        return {
            "prompt": prompt
        }
