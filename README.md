# 格星图 Skill（gexintu）

- 版本：V1.0.0
- 入库日期：2026-10-07
- 来源（事实来源）：`/Users/zengzhen/.agents/skills/gexintu`
- GitHub：`cur-line/gexintu-skill`（私有）

## 这是什么

制作可直接发布到视频号的中文星座 / 心理分析竖屏视频（账号「格星图」）。账号定调：温暖、克制、有生活细节的动态星刊；口播讲主线，画面用具体对象的变化补充情境、选择与后果。默认约 170–200 秒，硬上限 4 分钟。

## 内容

| 路径 | 说明 |
| --- | --- |
| `SKILL.md` | 制作规范：口播/画面文字/「初态 → 变化 → 结果」路线图、时长与节奏、画面与素材要求、交付检查 |
| `assets/illustrated-motion.html` | 动态星刊画面模板（HTML，供渲染使用） |
| `scripts/render_illustrated.py` | 竖屏视频渲染脚本 |
| `references/illustrated-workflow.md` | 图解式动态星刊工作流 |
| `references/editorial-demo-direction.md` | 编辑演示方向（选题与节奏参考） |

## 已排除

- 渲染中间产物与成片（`output/`、`render/`、`*.mp4`）、日志、`__pycache__`、`.DS_Store`
- 本机路径以外的私有素材与账号凭证（本技能不含任何密钥）

