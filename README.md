# AI Trend Video Toolkit

English | [中文](README.zh-CN.md)

Tools for remaking viral TikTok, YouTube Shorts and Instagram Reels trends: a clip-prep script, an AI-agent skill, and an honest list of the apps that put your face into trend videos.

> Made by the team behind [TrendTemplate](https://trendtemplate.com), one of the apps in the list below. The script and the skill work on their own; you don't need our site to use them.

- **[`trendclip.py`](trendclip.py)**: paste a TikTok / Shorts / Reels link, get the original clip cropped to 9:16 or 16:9, the original sound as MP3, every camera cut with its time, and a contact sheet. Also: one still per shot, a "trend vs me" side-by-side video, and a check of whether two videos share the same sound.
- **[`skills/trend-video`](skills/trend-video/SKILL.md)**: a skill for Claude Code, Codex and other coding agents. Ask "help me make the Wassup In A Minute video" and the agent finds the original, runs `trendclip`, names the song and picks the quickest way to make your version.
- **[AI trend video apps compared](#ai-apps-that-put-your-face-in-a-trend-video)** and a **[trend index](#trend-index)** with the song and origin of current trends.

## trendclip: get a trend clip ready to remake

Needs Python 3.9+, [ffmpeg](https://ffmpeg.org) and [yt-dlp](https://github.com/yt-dlp/yt-dlp). No pip packages.

```bash
brew install ffmpeg yt-dlp          # macOS; on Linux use your package manager or pip install yt-dlp
git clone https://github.com/ken-fs/ai-trend-video && cd ai-trend-video

python3 trendclip.py prep "https://www.tiktok.com/@nianaguerrero/video/7700194484528729345" --ratio 16:9 --short 7 --out wassup
```

```
1620x1080 15.0 s · 4 shots · cuts at 3.64 s, 7.2 s, 10.76 s
crop 1620x910 at (0,84) → 1280x720. Look at wassup/sheet.jpg to check nobody is cut off
wrote wassup/SHOTS.md and shots.json
```

What you get in the output folder:

| File | What it is |
|---|---|
| `original.mp4` | the downloaded clip, best quality available |
| `clip.mp4` / `clip.mp3` | cropped to your ratio at 720p, and the original sound |
| `clip-7s.mp4` / `clip-7s.mp3` | the first N seconds, with `--short N` |
| `sheet.jpg` | one frame every 0.5 s, to check the crop and see each move |
| `SHOTS.md` / `shots.json` | every shot with its start, end and length ([example](examples/wassup-SHOTS.md)) |

Options:

- `--ratio 9:16` (default), `16:9`, `1:1`, `4:5`, `3:4`. Cropping a wide group shot to 9:16 cuts people off; keep those 16:9.
- `--short 7` also exports the first 7 seconds. Pick a length that ends on a cut (see `SHOTS.md`).
- `--x-offset` / `--y-offset` move the crop when someone at the edge is cut off.
- `--threshold 0.25` is how big a change counts as a cut. Lower it (0.15) if a cut between two similar-looking shots is missed.
- `python3 trendclip.py cuts my_clip.mp4` prints the shot list of a file you already have.

### More commands

```bash
python3 trendclip.py frames wassup/clip.mp4 --out frames                 # one still per shot (storyboard, thumbnails, first frames)
python3 trendclip.py compare wassup/clip.mp4 my_version.mp4 --labels "Original,Me"   # "trend vs me", side by side
python3 trendclip.py compare wassup/clip.mp4 my_version.mp4 --layout stack           # one above the other
python3 trendclip.py match original.mp4 repost.mp4                       # same sound? where does one start in the other?
```

`match` compares the rhythm of the two sound tracks (bass, mids and highs separately), so it still works when a repost is re-encoded, quieter, or a few seconds shorter. Use it to find which post is the real original (reposts and AI remakes often have new footage over the old sound), or to find where a trend clip starts inside the full song. In our tests the same sound scored 0.82–1.00 and different dance tracks scored at most 0.41:

```
same sound: score 1.00; hey-boo-15s.mp3 starts 11.88 s into hey-boo-full.mp3
different sound: score 0.41
```

`compare --labels` needs an ffmpeg built with the `drawtext` filter; without it you get the same video without labels.

**Links that work:** TikTok, YouTube Shorts, Instagram Reels, Facebook, X, and most of the [sites yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). Local files work too. We tested TikTok, Shorts and Reels on 14 November 2026.

**If it asks you to log in:** some TikTok posts and most YouTube videos from a busy network need a logged-in browser. Add `--cookies-from-browser chrome` (or `firefox`, `safari`, `edge`). If YouTube keeps saying "Sign in to confirm you're not a bot", [export a cookies.txt](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies) and pass `--cookies cookies.txt`.

Only download clips you're allowed to use, and credit the creator when you post.

## The trend-video skill

Copy the folder into your agent's skills folder:

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -r skills/trend-video ~/.claude/skills/
# Codex / other agents that read skills: copy skills/trend-video wherever they load skills from
```

Then ask things like "make the Wassup In A Minute video with my friend", "what song is the Hotline Bling dance trend", or paste a link and say "I want to do this one". The skill tells the agent to find the real original (not a repost), get the song right (trend names are often misheard lyrics), run `trendclip`, then suggest filming it, editing it in CapCut, or an AI face swap, and go through a short checklist before posting (format, caption, credits, AI label).

## AI apps that put your face in a trend video

Checked on each app's own pages on 14 November 2026. Prices change, so check before you buy.

| App | How it works | Price on its site |
|---|---|---|
| [TrendTemplate](https://trendtemplate.com) (ours) | Upload 1–3 photos (pets on many templates). You get the real original clip with your face and its original sound, 5–30 s, 720p, no watermark. No free preview; failed renders refund the credits. | Credit packs: USD 4.99 (5 credits, one short clip), 9.99 (15, one full-length video), 19.99, 49.99. Credits don't expire. |
| [Jump on the Trend](https://jumponthetrend.app) | Trend templates with a free preview before you pay. | USD 6.99 for 100 credits; Pro USD 19.99/month for 300 credits. |
| [ViralRemix](https://viralremix.org) | Trend templates, many anime-style takes of each trend. | About USD 9.90 per video; packs of 4 for USD 29, 8 for USD 49. |
| [Starrd](https://www.getstarrd.app) | Trend templates, 1–3 people, pets on some. | Credit packs from USD 4.99 for 100 credits; the Wassup In A Minute template costs 150 credits. |
| [Flowlio](https://flowlioai.com) | Trend templates in 480p, 720p or 1080p. | Priced in credits (the Wassup In A Minute template: 600 credits at 480p on sale, 1,600 at 720p); no USD price on the template page. |
| [MakeViral](https://www.makeviral.ai) | A large template catalog, new trends almost daily. | Priced in credits per template; no USD price on the template page. |
| [CapCut](https://www.capcut.com) | User-made templates for most trends: you add your own photos or clips and it cuts them to the beat. | Free templates plus a paid Pro plan. |

Pick by what you want: your own photos and clips cut to the trend (CapCut), your face in the trend clip with its sound (TrendTemplate and the template sites above), or a free preview before paying (Jump on the Trend).

## Trend index

Current trends on TrendTemplate, each with a page that answers the usual questions (what the song is, who started it, how to make it). Lengths are the template lengths (short cut / full clip).

| Trend | Length | People | Guides |
|---|---|---|---|
| [Vlogmas Intro](https://trendtemplate.com/vlogmas-intro-ai) (cartoon Vlogmas intro, Welcome to Vlogmas intro, hand-drawn Vlogmas intro) | 7 s / 11 s | 1 | [Where it started](https://trendtemplate.com/vlogmas-intro-ai/trend) · [How to](https://trendtemplate.com/vlogmas-intro-ai/how-to) |
| [Frozen Viking Warrior](https://trendtemplate.com/frozen-viking-warrior-ai) (AI Frozen Viking Warrior effect, Viking filter, AI Nordic Ice Warrior effect) | 8 s | 1 | [Where it started](https://trendtemplate.com/frozen-viking-warrior-ai/trend) · [How to](https://trendtemplate.com/frozen-viking-warrior-ai/how-to) |
| [Boom Clap Confetti Vibe](https://trendtemplate.com/boom-clap-confetti-ai) (glam AI version from the CapCut template, Charli XCX Boom Clap AI trend) | 6 s / 13 s | 1 | [Song](https://trendtemplate.com/boom-clap-confetti-ai/song) · [Where it started](https://trendtemplate.com/boom-clap-confetti-ai/trend) · [How to](https://trendtemplate.com/boom-clap-confetti-ai/how-to) |
| [Boom Clap Trend (confetti cannon)](https://trendtemplate.com/boom-clap-confetti-cannon-ai) (Boom Clap trend, Boom Clap challenge, confetti cannon trend) | 6 s / 12 s | 1 | [Song](https://trendtemplate.com/boom-clap-confetti-ai/song) · [Where it started](https://trendtemplate.com/boom-clap-confetti-ai/trend) · [How to](https://trendtemplate.com/boom-clap-confetti-cannon-ai/how-to) |
| [No I Ain't Crazy YB](https://trendtemplate.com/no-i-aint-crazy-yb-ai) (No I ain't crazy I'm a 38 baby, 38 Baby AI trend, NBA YoungBoy AI trend, nba shelly) | 6 s / 12 s | 1 | [Song](https://trendtemplate.com/no-i-aint-crazy-yb-ai/song) · [Where it started](https://trendtemplate.com/no-i-aint-crazy-yb-ai/trend) · [How to](https://trendtemplate.com/no-i-aint-crazy-yb-ai/how-to) |
| [Goodbye GTA 5](https://trendtemplate.com/gta-5-goodbye-ai) (GTA 5 goodbye, GTA 5 farewell, sunset pier goodbye) | 10 s / 30 s | 1–2 | [Song](https://trendtemplate.com/gta-5-goodbye-ai/song) · [Where it started](https://trendtemplate.com/gta-5-goodbye-ai/trend) · [How to](https://trendtemplate.com/gta-5-goodbye-ai/how-to) |
| [Christmas Photobooth](https://trendtemplate.com/christmas-photobooth-ai) (Christmas photo booth trend, "Last Christmas" photobooth) | 7 s / 15 s | 1–2 | [Song](https://trendtemplate.com/christmas-photobooth-ai/song) · [Who started it](https://trendtemplate.com/christmas-photobooth-ai/trend) · [How to](https://trendtemplate.com/christmas-photobooth-ai/how-to) |
| [Pterodactyl Juárez](https://trendtemplate.com/pterodactyl-juarez-ai) (Pterodáctilo de Juárez, "ya lo agarré") | 7 s / 10 s | 1 | [Is it real? Origin](https://trendtemplate.com/pterodactyl-juarez-ai/trend) · [What "ya lo agarré" means](https://trendtemplate.com/pterodactyl-juarez-ai/ya-lo-agarre) · [How to](https://trendtemplate.com/pterodactyl-juarez-ai/how-to) |
| [Santa Nice List](https://trendtemplate.com/santa-nice-list-ai) ("quién se portó bien este año") | 7 s / 12 s | 1 or a pet | [Origin & timeline](https://trendtemplate.com/santa-nice-list-ai/trend) · [How to](https://trendtemplate.com/santa-nice-list-ai/how-to) · [Pet version](https://trendtemplate.com/santa-nice-list-ai/pets) |
| [Snowman Dance](https://trendtemplate.com/snowman-dance-ai) | 6 s / 12 s | 1–2 | [Song](https://trendtemplate.com/snowman-dance-ai/song) · [Dance tutorial](https://trendtemplate.com/snowman-dance-ai/tutorial) · [How to](https://trendtemplate.com/snowman-dance-ai/how-to) |
| [Jingle Bell Brazil Dance](https://trendtemplate.com/jingle-bell-brazil-dance-ai) | 7 s / 15 s | 1–3 (one photo = you in all three spots) | [Song](https://trendtemplate.com/jingle-bell-brazil-dance-ai/song) · [Who started it](https://trendtemplate.com/jingle-bell-brazil-dance-ai/trend) · [How to](https://trendtemplate.com/jingle-bell-brazil-dance-ai/how-to) |
| [Santa Hug](https://trendtemplate.com/santa-hug-ai) | 7 s / 12 s | 1 | [What it is](https://trendtemplate.com/santa-hug-ai/trend) · [How to](https://trendtemplate.com/santa-hug-ai/how-to) · [Christmas card ideas](https://trendtemplate.com/santa-hug-ai/christmas-card) |
| [Need for Speed AI](https://trendtemplate.com/need-for-speed-ai) | 7 s / 14 s | 1 car photo (cars, trucks, SUVs) | [The movie & the car](https://trendtemplate.com/need-for-speed-ai/movie) · [Origin & timeline](https://trendtemplate.com/need-for-speed-ai/trend) · [How to](https://trendtemplate.com/need-for-speed-ai/how-to) |
| [Wassup In A Minute](https://trendtemplate.com/wassup-in-a-minute-ai) | 7 s / 15 s | 1–2 + pets | [Song](https://trendtemplate.com/wassup-in-a-minute-ai/song) · [Origin & timeline](https://trendtemplate.com/wassup-in-a-minute-ai/trend) · [How to](https://trendtemplate.com/wassup-in-a-minute-ai/how-to) |
| [Waist Heart](https://trendtemplate.com/waist-heart-ai) | 9 s | 1 | [Origin & timeline](https://trendtemplate.com/waist-heart-ai/trend) · [How to](https://trendtemplate.com/waist-heart-ai/how-to) |
| [Drake Hotline Bling Dance](https://trendtemplate.com/drake-hotline-bling-dance-ai) | 7 s / 14 s | 1 | [Song](https://trendtemplate.com/drake-hotline-bling-dance-ai/song) · [Origin & timeline](https://trendtemplate.com/drake-hotline-bling-dance-ai/trend) · [How to](https://trendtemplate.com/drake-hotline-bling-dance-ai/how-to) |
| [Christmas Pajama Dance](https://trendtemplate.com/christmas-pajama-dance-ai) | 7 s / 14 s | 1–2 + pets | [Song](https://trendtemplate.com/christmas-pajama-dance-ai/song) · [Origin & timeline](https://trendtemplate.com/christmas-pajama-dance-ai/trend) · [How to](https://trendtemplate.com/christmas-pajama-dance-ai/how-to) |
| [Hey Boo Come Slide With Me](https://trendtemplate.com/hey-boo-come-slide-with-me-ai) | 15 s / 27 s | 1–2 + pets | [Song](https://trendtemplate.com/hey-boo-come-slide-with-me-ai/song) · [Origin & timeline](https://trendtemplate.com/hey-boo-come-slide-with-me-ai/trend) · [How to](https://trendtemplate.com/hey-boo-come-slide-with-me-ai/how-to) |
| [Shoulder Carry](https://trendtemplate.com/shoulder-carry-trend-ai) | 9 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/shoulder-carry-trend-ai/trend) · [How to](https://trendtemplate.com/shoulder-carry-trend-ai/how-to) |
| [I Love the Smiths](https://trendtemplate.com/i-love-the-smiths-ai) | 6 s / 25 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/i-love-the-smiths-ai/trend) · [How to](https://trendtemplate.com/i-love-the-smiths-ai/how-to) |
| [Pimpwalk Entrance](https://trendtemplate.com/pimpwalk-entrance-ai) | 7 s / 15 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/pimpwalk-entrance-ai/trend) · [How to](https://trendtemplate.com/pimpwalk-entrance-ai/how-to) |
| [Fish Cutting Meme](https://trendtemplate.com/fish-cutting-meme-ai) | 6 s / 10 s | 1 + pets | [Origin & timeline](https://trendtemplate.com/fish-cutting-meme-ai/trend) · [How to](https://trendtemplate.com/fish-cutting-meme-ai/how-to) |
| [Wipe Me Down](https://trendtemplate.com/wipe-me-down-ai) | 6 s / 15 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/wipe-me-down-ai/trend) · [How to](https://trendtemplate.com/wipe-me-down-ai/how-to) |
| [Santa Couple Dance](https://trendtemplate.com/santa-couple-dance-ai) | 7 s / 15 s | 1–2 + pets | — |
| [Elf Dance](https://trendtemplate.com/elf-dance-ai) | 7 s / 15 s | 1–3 | [How to](https://trendtemplate.com/elf-dance-ai/how-to) |
| [End of Watch](https://trendtemplate.com/end-of-watch-ai) | 6 s / 11 s | 1–2 + pets | [Song](https://trendtemplate.com/end-of-watch-ai/song) · [Origin & timeline](https://trendtemplate.com/end-of-watch-ai/trend) · [How to](https://trendtemplate.com/end-of-watch-ai/how-to) · [With a friend](https://trendtemplate.com/end-of-watch-ai/with-a-friend) |
| [Alors On Danse](https://trendtemplate.com/alors-on-danse-ai) | 6 s / 15 s | 1–2 + pets | [How to](https://trendtemplate.com/alors-on-danse-ai/how-to) |
| [Smalltown Boy AI](https://trendtemplate.com/smalltown-boy-ai) | 20 s | 1–2 | [How to](https://trendtemplate.com/smalltown-boy-ai/how-to) |
| [Ozil Goal AI](https://trendtemplate.com/ozil-goal-ai) | 10 s | 1 | [How to](https://trendtemplate.com/ozil-goal-ai/how-to) |
| [Make It Cap](https://trendtemplate.com/make-it-cap-ai) | 6 s / 12 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/make-it-cap-ai/trend) · [How to](https://trendtemplate.com/make-it-cap-ai/how-to) |
| [Tiny Desk](https://trendtemplate.com/tiny-desk-concert-ai) | 6 s / 19 s | 1–3 + pets | [Origin & timeline](https://trendtemplate.com/tiny-desk-concert-ai/trend) · [How to](https://trendtemplate.com/tiny-desk-concert-ai/how-to) · [The band](https://trendtemplate.com/tiny-desk-concert-ai/band) |
| [Dime Dime Baby](https://trendtemplate.com/dime-dime-baby-ai) | 7 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/dime-dime-baby-ai/trend) · [How to](https://trendtemplate.com/dime-dime-baby-ai/how-to) |
| [Bulin 47](https://trendtemplate.com/bulin-47-ai) | 5 s / 30 s | 1 | [Origin & timeline](https://trendtemplate.com/bulin-47-ai/trend) · [How to](https://trendtemplate.com/bulin-47-ai/how-to) |
| [Hotel Lobby](https://trendtemplate.com/hotel-lobby-ai) | 6 s / 21 s | 1–2 + pets | [Origin & timeline](https://trendtemplate.com/hotel-lobby-ai/trend) · [How to](https://trendtemplate.com/hotel-lobby-ai/how-to) · [Prompt](https://trendtemplate.com/hotel-lobby-ai/prompt) · [Apps compared](https://trendtemplate.com/hotel-lobby-ai/apps) |

## License

MIT. See [LICENSE](LICENSE). Trend clips, songs and artwork belong to their creators; this repo only contains code and text.
