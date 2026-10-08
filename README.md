# 格星图 gexintu

制作星座情感心理类中文竖屏视频的 AI 技能：原创共鸣文案、生活照片与语义动画、配音混音、封面以及视频号发布文案。

默认新片少于三分钟，12–18个有叙事作用的画面段，1080×1920 / 30fps。主入口是 [SKILL.md](SKILL.md)，详细导演、音频、策划和验收说明放在 `references/`。

## 安装

把仓库安装到所用智能体识别的 skills 目录下，目录名为 `gexintu`。已有安装请在原工作树更新，不另建会漂移的副本。技能不绑定具体模型；需要 Hypit、HyperFrames 或图像生成时使用对应工具及技能。

## 可选 canvas 渲染器

需要 Python 3.10+、ffmpeg/ffprobe、Playwright 和 Chromium：

```sh
python3 -m pip install playwright
python3 -m playwright install chromium
python3 scripts/render_illustrated.py --help
python3 scripts/render_illustrated.py --project /path/to/episode --audit --preview 0,1,3
python3 scripts/render_illustrated.py --project /path/to/episode --render /path/to/episode/outputs/video-v2.mp4
python3 scripts/verify_delivery.py /path/to/episode/outputs/video-v2.mp4
```

输入字段见 [模板说明](references/illustrated-workflow.md)。渲染器仅消费项目内图片、时间轴和已混好的本地音轨；不会自动调用付费服务、生成配音或发布视频。缺依赖时如实报告，不能声称已出片。

公开仓库只包含规范、代码和模板，不包含成片、私有参考音频、人物素材或服务密钥。服务凭据使用外部环境配置；引用素材和克隆音频须在当前项目中获得适当使用授权。

版本：V1.2.0。沉淀 9 大内容栏目与 222 条选题库于 `references/content-system-and-topics.md`。历史V1.0.0保留于 `archive-v1.0.0` 标签，可用 `git show archive-v1.0.0:SKILL.md` 查阅；旧个人路径与过期参数只作历史记录。
