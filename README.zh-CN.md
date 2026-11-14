# AI 热梗视频工具包

[English](README.md) | 中文

用来翻拍 TikTok、YouTube Shorts、Instagram Reels 热梗视频的一套东西：一个原片准备脚本、一个给 AI 编程助手用的 skill，还有一份如实写的「把你的脸放进热梗视频」的工具对比。

> 由 [TrendTemplate](https://trendtemplate.com) 团队制作，下面对比表里也有我们自己的产品。脚本和 skill 不依赖我们的网站，单独就能用。

- **[`trendclip.py`](trendclip.py)**：贴一个 TikTok / Shorts / Reels 链接，拿到裁成 9:16 或 16:9 的原片、原声 MP3、每个镜头的切换时间，还有一张逐镜头预览图。
- **[`skills/trend-video`](skills/trend-video/SKILL.md)**：给 Claude Code、Codex 等 AI 编程助手用的 skill。跟它说「帮我做 Wassup In A Minute 的视频」，它会去找原片、跑 `trendclip`、告诉你是什么歌，再给出最省事的做法。
- 下面还有 **[AI 热梗视频工具对比](#把你的脸放进热梗视频的-ai-工具)** 和 **[热梗索引](#热梗索引)**（当前热梗的歌名和来历）。

## trendclip：把热梗原片准备好

需要 Python 3.9+、[ffmpeg](https://ffmpeg.org) 和 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，不用装任何 pip 包。

```bash
brew install ffmpeg yt-dlp          # macOS；Linux 用系统的包管理器，或 pip install yt-dlp
git clone https://github.com/ken-fs/ai-trend-video && cd ai-trend-video

python3 trendclip.py prep "https://www.tiktok.com/@nianaguerrero/video/7700194484528729345" --ratio 16:9 --short 7 --out wassup
```

```
1620x1080 15.0 s · 4 shots · cuts at 3.64 s, 7.2 s, 10.76 s
crop 1620x910 at (0,84) → 1280x720. Look at wassup/sheet.jpg to check nobody is cut off
wrote wassup/SHOTS.md and shots.json
```

输出文件夹里有这些：

| 文件 | 是什么 |
|---|---|
| `original.mp4` | 下载下来的原片，能拿到的最高画质 |
| `clip.mp4` / `clip.mp3` | 按你选的比例裁好、720p 的视频，和原声 |
| `clip-7s.mp4` / `clip-7s.mp3` | 加 `--short 7` 时多导出的前 7 秒 |
| `sheet.jpg` | 每 0.5 秒一帧的预览图，用来检查有没有人被裁掉、看清每个动作 |
| `SHOTS.md` / `shots.json` | 每个镜头的开始、结束时间和长度（[示例](examples/wassup-SHOTS.md)） |

参数：

- `--ratio`：`9:16`（默认）、`16:9`、`1:1`、`4:5`、`3:4`。横屏的多人画面裁成 9:16 会把两边的人裁掉，这种保留 16:9。
- `--short 7`：再导出前 7 秒。长度最好正好停在镜头切换处（看 `SHOTS.md`），停在镜头开头不到一秒会像剪错了。
- `--x-offset` / `--y-offset`：画面边上的人被裁掉时，左右 / 上下挪动裁切框。
- `--threshold 0.25`：画面变化多大算一次切换。两个镜头长得很像、没被认出来时调低到 0.15。
- `python3 trendclip.py cuts my_clip.mp4`：只看手上已有视频的镜头表。

**支持哪些链接**：TikTok、YouTube Shorts、Instagram Reels、Facebook、X，以及 [yt-dlp 支持的](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)大多数网站，本地视频文件也行。TikTok、Shorts、Reels 我们 2026 年 11 月 14 日都实测过。

**要求登录时**：有些 TikTok 帖子、以及很多 YouTube 视频（网络繁忙时）要已登录的浏览器才能下。加上 `--cookies-from-browser chrome`（也可以是 `firefox`、`safari`、`edge`）。YouTube 一直提示「Sign in to confirm you're not a bot」的话，[导出 cookies.txt](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)，再加 `--cookies cookies.txt`。

只下载你有权使用的视频，发布时注明原作者。

## trend-video skill

把文件夹复制到 AI 助手读取 skill 的目录：

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -r skills/trend-video ~/.claude/skills/
# Codex 或其它支持 skill 的助手：把 skills/trend-video 放到它加载 skill 的位置
```

然后就可以这样问：「帮我和朋友做 Wassup In A Minute 的视频」「Hotline Bling 那个舞是什么歌」，或者直接贴一个链接说「我想做这个」。skill 里写的是 AI 该怎么做：先找到真正的原片（不是转发），把歌名说对（梗名经常是把歌词听错了），跑 `trendclip`，再根据你要的给出做法：自己拍、用 CapCut 剪，或者用 AI 换脸。skill 本身是英文写的，你用中文问，助手照样用中文回答。

## 把你的脸放进热梗视频的 AI 工具

2026 年 11 月 14 日在各家自己的页面上核对的，价格会变，买之前再看一眼。

| 工具 | 怎么用 | 官网写的价格 |
|---|---|---|
| [TrendTemplate](https://trendtemplate.com/zh)（我们的） | 传 1–3 张照片（很多模板也能用宠物），拿到换上你的脸、带原声的真实原片，5–30 秒，720p，无水印。没有免费预览；生成失败积分自动退回。 | 积分包：USD 4.99（5 积分，一条短版）、9.99（15 积分，一条完整版）、19.99、49.99。积分不过期。 |
| [Jump on the Trend](https://jumponthetrend.app) | 热梗模板，付款前可以免费预览。 | USD 6.99 买 100 积分；Pro 每月 USD 19.99，300 积分。 |
| [ViralRemix](https://viralremix.org) | 热梗模板，很多梗有多个动漫风格版本。 | 每条约 USD 9.90；4 条 USD 29，8 条 USD 49。 |
| [Starrd](https://www.getstarrd.app) | 热梗模板，1–3 人，部分能用宠物。 | 积分包 USD 4.99 / 100 积分起；Wassup In A Minute 模板一条 150 积分。 |
| [Flowlio](https://flowlioai.com) | 热梗模板，有 480p、720p、1080p。 | 按积分收（Wassup In A Minute 模板 480p 促销价 600 积分，720p 1,600 积分）；模板页没写美元价。 |
| [MakeViral](https://www.makeviral.ai) | 模板很多，几乎每天上新梗。 | 每个模板按积分收；模板页没写美元价。 |
| [CapCut](https://www.capcut.com) | 大多数热梗都有用户做的模板：放进你自己的照片或视频，它按节拍剪好。 | 有免费模板，另有付费 Pro。 |

按你想要的选：用自己的照片和视频剪出同款（CapCut）；把你的脸换进热梗原片、带原声（TrendTemplate 和上面几家模板站）；想先免费看效果再付钱（Jump on the Trend）。

## 热梗索引

TrendTemplate 上现有的热梗，每个都有一页回答常见问题（是什么歌、谁先开始的、怎么做）。时长是模板的时长（短版 / 完整版）。

| 热梗 | 时长 | 人数 | 攻略 |
|---|---|---|---|
| [Wassup In A Minute](https://trendtemplate.com/zh/wassup-in-a-minute-ai) | 7 秒 / 15 秒 | 1–2 人，可用宠物 | [是什么歌](https://trendtemplate.com/zh/wassup-in-a-minute-ai/song) · [来历和时间线](https://trendtemplate.com/zh/wassup-in-a-minute-ai/trend) · [怎么做](https://trendtemplate.com/zh/wassup-in-a-minute-ai/how-to) |
| [Waist Heart](https://trendtemplate.com/zh/waist-heart-ai) | 9 秒 | 1 人 | [来历和时间线](https://trendtemplate.com/zh/waist-heart-ai/trend) · [怎么做](https://trendtemplate.com/zh/waist-heart-ai/how-to) |
| [Drake Hotline Bling Dance](https://trendtemplate.com/zh/drake-hotline-bling-dance-ai) | 7 秒 / 14 秒 | 1 人 | [是什么歌](https://trendtemplate.com/zh/drake-hotline-bling-dance-ai/song) · [来历和时间线](https://trendtemplate.com/zh/drake-hotline-bling-dance-ai/trend) · [怎么做](https://trendtemplate.com/zh/drake-hotline-bling-dance-ai/how-to) |
| [Christmas Pajama Dance](https://trendtemplate.com/zh/christmas-pajama-dance-ai) | 7 秒 / 14 秒 | 1–2 人，可用宠物 | [是什么歌](https://trendtemplate.com/zh/christmas-pajama-dance-ai/song) · [来历和时间线](https://trendtemplate.com/zh/christmas-pajama-dance-ai/trend) · [怎么做](https://trendtemplate.com/zh/christmas-pajama-dance-ai/how-to) |
| [Hey Boo Come Slide With Me](https://trendtemplate.com/zh/hey-boo-come-slide-with-me-ai) | 15 秒 / 27 秒 | 1–2 人，可用宠物 | [是什么歌](https://trendtemplate.com/zh/hey-boo-come-slide-with-me-ai/song) · [来历和时间线](https://trendtemplate.com/zh/hey-boo-come-slide-with-me-ai/trend) · [怎么做](https://trendtemplate.com/zh/hey-boo-come-slide-with-me-ai/how-to) |
| [Shoulder Carry](https://trendtemplate.com/zh/shoulder-carry-trend-ai) | 9 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/shoulder-carry-trend-ai/trend) · [怎么做](https://trendtemplate.com/zh/shoulder-carry-trend-ai/how-to) |
| [I Love the Smiths](https://trendtemplate.com/zh/i-love-the-smiths-ai) | 6 秒 / 25 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/i-love-the-smiths-ai/trend) · [怎么做](https://trendtemplate.com/zh/i-love-the-smiths-ai/how-to) |
| [Pimpwalk Entrance](https://trendtemplate.com/zh/pimpwalk-entrance-ai) | 7 秒 / 15 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/pimpwalk-entrance-ai/trend) · [怎么做](https://trendtemplate.com/zh/pimpwalk-entrance-ai/how-to) |
| [Fish Cutting Meme](https://trendtemplate.com/zh/fish-cutting-meme-ai) | 6 秒 / 10 秒 | 1 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/fish-cutting-meme-ai/trend) · [怎么做](https://trendtemplate.com/zh/fish-cutting-meme-ai/how-to) |
| [Wipe Me Down](https://trendtemplate.com/zh/wipe-me-down-ai) | 6 秒 / 15 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/wipe-me-down-ai/trend) · [怎么做](https://trendtemplate.com/zh/wipe-me-down-ai/how-to) |
| [Santa Couple Dance](https://trendtemplate.com/zh/santa-couple-dance-ai) | 7 秒 / 15 秒 | 1–2 人，可用宠物 | — |
| [Elf Dance](https://trendtemplate.com/zh/elf-dance-ai) | 7 秒 / 15 秒 | 1–3 人 | [怎么做](https://trendtemplate.com/zh/elf-dance-ai/how-to) |
| [End of Watch](https://trendtemplate.com/zh/end-of-watch-ai) | 6 秒 / 11 秒 | 1–2 人，可用宠物 | [是什么歌](https://trendtemplate.com/zh/end-of-watch-ai/song) · [来历和时间线](https://trendtemplate.com/zh/end-of-watch-ai/trend) · [怎么做](https://trendtemplate.com/zh/end-of-watch-ai/how-to) · [和朋友一起](https://trendtemplate.com/zh/end-of-watch-ai/with-a-friend) |
| [Alors On Danse](https://trendtemplate.com/zh/alors-on-danse-ai) | 6 秒 / 15 秒 | 1–2 人，可用宠物 | [怎么做](https://trendtemplate.com/zh/alors-on-danse-ai/how-to) |
| [Smalltown Boy AI](https://trendtemplate.com/zh/smalltown-boy-ai) | 20 秒 | 1–2 人 | [怎么做](https://trendtemplate.com/zh/smalltown-boy-ai/how-to) |
| [Ozil Goal AI](https://trendtemplate.com/zh/ozil-goal-ai) | 10 秒 | 1 人 | [怎么做](https://trendtemplate.com/zh/ozil-goal-ai/how-to) |
| [Make It Cap](https://trendtemplate.com/zh/make-it-cap-ai) | 6 秒 / 12 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/make-it-cap-ai/trend) · [怎么做](https://trendtemplate.com/zh/make-it-cap-ai/how-to) |
| [Tiny Desk](https://trendtemplate.com/zh/tiny-desk-concert-ai) | 6 秒 / 19 秒 | 1–3 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/tiny-desk-concert-ai/trend) · [怎么做](https://trendtemplate.com/zh/tiny-desk-concert-ai/how-to) · [乐队](https://trendtemplate.com/zh/tiny-desk-concert-ai/band) |
| [Dime Dime Baby](https://trendtemplate.com/zh/dime-dime-baby-ai) | 7 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/dime-dime-baby-ai/trend) · [怎么做](https://trendtemplate.com/zh/dime-dime-baby-ai/how-to) |
| [Bulin 47](https://trendtemplate.com/zh/bulin-47-ai) | 5 秒 / 30 秒 | 1 人 | [来历和时间线](https://trendtemplate.com/zh/bulin-47-ai/trend) · [怎么做](https://trendtemplate.com/zh/bulin-47-ai/how-to) |
| [Hotel Lobby](https://trendtemplate.com/zh/hotel-lobby-ai) | 6 秒 / 21 秒 | 1–2 人，可用宠物 | [来历和时间线](https://trendtemplate.com/zh/hotel-lobby-ai/trend) · [怎么做](https://trendtemplate.com/zh/hotel-lobby-ai/how-to) · [提示词](https://trendtemplate.com/zh/hotel-lobby-ai/prompt) · [工具对比](https://trendtemplate.com/zh/hotel-lobby-ai/apps) |

## 许可证

MIT，见 [LICENSE](LICENSE)。热梗原片、歌曲和画作归原作者所有，本仓库只包含代码和文字。
