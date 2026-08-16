#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 collect_fonts.ps1 导出的 JSON 生成单页字体展示站 index.html。"""

import json
import pathlib
import re
import sys
import datetime

SYMBOL_HINTS = (
    "wingdings", "webdings", "marlett", "mt extra", "sorts", "bookshelf",
    "emoji", "mdl2", "fluent icons", "segoe ui symbol", "outlook",
    "symbol", "dingbat", "reference specialty",
)

# 每个分类的正则模式：英文词用 \b 词边界，避免误伤（如 unicode 含 code、Monotype 含 mono）
CAT_PATTERNS = {
    "mono": [
        r"\bmono\b", r"\bconsol\w*", r"\bcourier\b", r"\bcascadia\b",
        r"\bcode\b", r"\bterminal\b", r"\bconsole\b", r"lucida console",
        r"\binconsolata\b", r"nimbus mono", r"\bocr\b",
    ],
    "display": [
        r"\bdisplay\b", r"\bimpact\b", r"\bstencil\b", r"\balgerian\b",
        r"\bbauhaus\b", r"\bchiller\b", r"\bcooper\b", r"\bjokerman\b",
        r"\bmagnet\b", r"old english", r"\bblackletter\b", r"\bfraktur\b",
        r"\bshowcard\b", r"\bhaettenschweiler\b", r"\bagency\b",
        r"\bblackadder\b", r"\bbraggadocio\b", r"\bbroadway\b", r"\bcuriz\b",
        r"\bengravers\b", r"felix titling", r"\bpapyrus\b", r"bodoni poster",
        r"\bcastellar\b", r"\bharlow\b", r"\bkunstler\b", r"\bmatura\b",
        r"snap itc", r"\btrajan\b", r"\bvivaldi\b", r"\bcurlz\b",
        r"\bbritannic\b", r"\bcolonna\b", r"\bforte\b", r"\bgigi\b",
        r"\bharrington\b", r"\bjuice\b", r"\bmaiandra\b", r"\bgabriola\b",
        r"\bmagneto\b",
        r"\bniagara\b", r"\bonyx\b", r"\bparchment\b", r"\bplaybill\b",
        r"\bwide latin\b", r"\belephant\b", r"\bravie\b", "xingkai",
        "琥珀", "隶书", "新魏", "行楷", "幼圆", "彩云", "华文彩云",
        "华文琥珀", "华文隶书", "华文新魏", "华文行楷", "caiyun", "hupo",
        "liti", "xinwei", "lisu", "youyuan",
    ],
    "hand": [
        r"\bscript\b", r"\bbrush\b", r"\bhand\b", r"\bcursive\b",
        r"\bcalligraphy\b", r"\bchancery\b", r"\bcomic\b", r"\bmarker\b",
        r"\bpen\b", r"\bkai\b", r"\bcorsiva\b", r"\bmistral\b", r"\bhandw",
        r"\brage\b", r"\bpristina\b", r"\binformal\b", r"ink free",
        r"\bkristen\b", "segoe print", "segoe script", "kaiti", "shuti",
        "yaoti", "楷", "草", "舒体", "姚体",
    ],
    "sans": [
        r"\bsans\b", r"\barial\b", r"\bhelvetica\b", r"\bverdana\b",
        r"\btahoma\b", r"\bsegoe\b", r"\btrebuchet\b", r"\bcalibri\b",
        r"\bcandara\b", r"\bcorbel\b", r"\bgill\b", r"\bfutura\b",
        r"century gothic", r"franklin gothic", r"\bbahnschrift\b",
        r"\bavenir\b", r"\bmyriad\b", r"\broboto\b", r"\blato\b",
        r"source sans", r"noto sans", r"droid sans", "黑", "hei", "gothic",
        "雅黑", "yahei", "正黑", "等线", "dengxian", "细黑", "微軟正黑",
        "微软雅黑", "黑体", r"\bebrima\b", r"\bgadugi\b",
        r"\bleelawadee\b", r"\bnirmala\b", r"\bmyanmar\b", r"\bjavanese\b",
        r"\bhimalaya\b", r"tai le", r"tai lue", r"\bphagspa\b",
        r"\buighur\b", r"yi baiti", r"\bmongolian\b", r"mv boli",
        r"\bdubai\b", r"tw cen", r"\beras\b",
    ],
    "serif": [
        r"\bserif\b", r"\btimes\b", r"\bgeorgia\b", r"\bgaramond\b",
        r"\bpalatino\b", r"\bbookman\b", r"\bcambria\b", r"\bconstantia\b",
        r"\bdidot\b", r"\bbodoni\b", r"\bbaskerville\b", r"\bcaslon\b",
        r"\bgoudy\b", r"\brockwell\b", r"\bslab\b", r"\bsong\b", r"\bming\b",
        "宋", "明", "仿宋", r"\bsimsun\b", "fangsong", "dengxian serif",
        r"\bperpetua\b", r"\bsylfaen\b", r"\bsitka\b", "berkeley oldstyle",
        r"\bbell\b", r"\bantiqua\b", r"\bcentury\b", r"\bschoolbook\b",
        r"\bcalisto\b", r"\bbright\b", r"\bfax\b", r"modern no\. 20",
        r"poor richard", r"high tower", r"\bimprint\b", r"\bfootlight\b",
        r"\bbernard\b", r"\bcalifornian\b", r"\bcentaur\b", "nsimsun",
        "mingliu", "pmingliu", "stsong", "zhongsong",
    ],
}


def classify(name: str) -> str:
    n = name.lower()
    if any(h in n for h in SYMBOL_HINTS):
        return "symbol"
    for cat in ("mono", "display", "hand", "sans", "serif"):
        if any(re.search(p, n) for p in CAT_PATTERNS[cat]):
            return cat
    return "other"


# 中文字体首字 → 拼音，用于把中文字体置顶并按键位排序
PINYIN_FIRST = {
    "得": "de", "等": "deng", "方": "fang", "仿": "fang", "汉": "han",
    "黑": "hei", "华": "hua", "经": "jing", "楷": "kai", "理": "li",
    "隶": "li", "三": "san", "思": "si", "宋": "song", "甜": "tian",
    "微": "wei", "細": "xi", "新": "xin", "幼": "you", "造": "zao",
    "张": "zhang", "★": "zzz",
}
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def sort_key(font: dict):
    name = font["name"]
    if CJK_RE.search(name):
        return (0, PINYIN_FIRST.get(name[0], "zzzz"), name.casefold())
    return (1, "", name.casefold())


def main():
    data_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.home() / "fonts_data.json"
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("index.html")

    with open(data_path, encoding="utf-8-sig") as f:
        raw = json.load(f)

    fonts = []
    for item in raw:
        name = str(item["Name"]).strip()
        if not name:
            continue
        zh = str(item.get("ZhName") or "").strip()
        cat = classify(name)
        if cat == "symbol":
            continue
        files = [str(x) for x in item.get("Files") or []]
        font = {"name": name, "files": files, "cat": cat}
        if zh and zh.casefold() != name.casefold():
            font["zh"] = zh
        fonts.append(font)

    fonts.sort(key=sort_key)

    CATS = [
        ("sans", "无衬线"),
        ("serif", "衬线"),
        ("mono", "等宽"),
        ("hand", "手写"),
        ("display", "展示"),
        ("other", "其他"),
    ]

    fonts_json = json.dumps(fonts, ensure_ascii=True).replace("</", "<\\/")
    cats_json = json.dumps(CATS, ensure_ascii=True)
    today = datetime.date.today().isoformat()

    TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>本机字体 · Font Gallery</title>
<style>
:root{
  --bg:#f4f2ec;
  --card:#ffffff;
  --ink:#211e18;
  --mut:#8b8578;
  --line:#e7e3d8;
  --acc:#b45309;
  --fs:32px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif;
  line-height:1.5}
button,input{font:inherit;color:inherit}
button{cursor:pointer;background:none;border:none;padding:0}

/* ---------- top bar ---------- */
header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.9);
  -webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line)}
.top-inner{max-width:1500px;margin:0 auto;padding:14px 20px 0}
.head-row{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:26px;margin:0;letter-spacing:.5px}
h1 .dot{color:var(--acc)}
.sub{font-size:13px;color:var(--mut)}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;padding:14px 0 10px}
.ctrl{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--mut);white-space:nowrap}
.ctrl.grow{flex:1;min-width:260px}
.ctrl.grow .text-input{width:100%;min-width:0}
input[type=search],.text-input{
  border:1px solid var(--line);border-radius:9px;padding:7px 11px;
  background:#fbfaf6;min-width:220px;outline:none}
input[type=search]:focus,.text-input:focus{border-color:var(--acc);background:#fff}
input[type=range]{accent-color:var(--acc)}
.size-val{min-width:34px;text-align:right;font-variant-numeric:tabular-nums}
.seg{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;background:#fbfaf6}
.seg button{padding:7px 12px;font-size:13px;border-right:1px solid var(--line);color:var(--mut)}
.seg button:last-child{border-right:none}
.seg button.on{background:var(--ink);color:#fff}
#italicBtn{font-style:italic;font-family:Georgia,serif;min-width:38px}
.zh-chip{margin-left:auto}
.chips{display:flex;gap:8px;flex-wrap:wrap;padding-bottom:12px}
.chip{border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:13px;
  background:#fff;color:var(--mut)}
.chip:hover{border-color:var(--acc);color:var(--acc)}
.chip.on{background:var(--ink);border-color:var(--ink);color:#fff}
.chip .n{opacity:.55;margin-left:4px;font-size:11px}

/* ---------- grid ---------- */
main{max-width:1500px;margin:0 auto;padding:20px}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;
  cursor:pointer;transition:box-shadow .18s ease,transform .18s ease;
  content-visibility:auto;contain-intrinsic-size:238px}
.card:hover,.card:focus-visible{box-shadow:0 10px 28px rgba(33,30,24,.1);transform:translateY(-2px)}
.card:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.card.hide{display:none}
.preview{padding:20px 18px 16px;min-height:150px;display:flex;align-items:center;justify-content:center}
.sample{max-width:100%;text-align:center;overflow:hidden}
.sample .row{line-height:1.3;word-break:break-word;overflow-wrap:anywhere}
.sample .row + .row{margin-top:6px}
.sample .row.empty{display:none}
.meta{display:flex;align-items:center;justify-content:space-between;gap:10px;
  padding:9px 14px;border-top:1px solid var(--line);font-size:12px;color:var(--mut)}
.meta .names{display:flex;flex-direction:column;min-width:0;gap:2px}
.meta .name{font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.meta .en{font-size:11px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.meta .en:empty{display:none}
.meta .tags{display:flex;gap:6px;align-items:center;flex-shrink:0}
.tag{border:1px solid var(--line);border-radius:6px;padding:2px 7px;background:#faf8f2;
  color:var(--mut);font-size:11px}
.tag.file{max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#empty{display:none;text-align:center;padding:70px 20px;color:var(--mut)}
#empty.show{display:block}
#empty .big{font-size:40px;margin-bottom:8px}
footer{max-width:1500px;margin:0 auto;padding:26px 20px 44px;color:var(--mut);font-size:12.5px;
  border-top:1px solid var(--line)}

/* ---------- modal ---------- */
#modal{position:fixed;inset:0;z-index:100;display:none}
#modal.show{display:flex;align-items:center;justify-content:center;padding:24px}
.backdrop{position:absolute;inset:0;background:rgba(33,30,24,.45);
  -webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.panel{position:relative;background:#fff;border-radius:18px;max-width:860px;width:100%;
  padding:30px 34px 24px;box-shadow:0 24px 80px rgba(0,0,0,.28);max-height:86vh;overflow:auto}
#mClose{position:absolute;top:14px;right:16px;font-size:24px;color:var(--mut);
  width:38px;height:38px;border-radius:50%;line-height:1}
#mClose:hover{background:#f2efe7;color:var(--ink)}
#mName{font-size:30px;font-weight:700;margin:0 44px 0 0;word-break:break-word}
#mName small{font-size:13px;color:var(--mut);font-weight:400;margin-left:10px}
#mSample{margin-top:22px;font-size:44px;line-height:1.35;min-height:120px;
  word-break:break-word}
#mSample .row + .row{margin-top:12px}
#mSample .row.empty{display:none}
#mMeta{margin-top:20px;font-size:13px;color:var(--mut);border-top:1px solid var(--line);padding-top:14px}
#mMeta b{color:var(--ink);font-weight:600}

@media (max-width:640px){
  #grid{grid-template-columns:1fr}
  h1{font-size:22px}
  .zh-chip{margin-left:0}
  .panel{padding:24px 18px 18px}
  #mSample{font-size:26px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>

<header>
  <div class="top-inner">
    <div class="head-row">
      <h1>本机字体<span class="dot"> · </span>Font Gallery</h1>
      <span class="sub" id="sub"></span>
    </div>
    <div class="controls">
      <div class="ctrl">
        <input type="search" id="q" placeholder="搜索字体名称或文件名…" aria-label="搜索字体">
      </div>
      <div class="ctrl grow">
        <span>示例文字</span>
        <input class="text-input" id="sample" type="text" aria-label="示例文字">
      </div>
      <div class="ctrl">
        <span>字号</span>
        <input type="range" id="size" min="12" max="72" value="32" aria-label="字号">
        <span class="size-val" id="sizeVal">32</span>
      </div>
      <div class="seg" role="group" aria-label="字重">
        <button data-w="400" class="on" title="常规">常规</button>
        <button data-w="700" title="粗体">粗体</button>
      </div>
      <div class="seg" role="group" aria-label="样式">
        <button id="italicBtn" title="斜体">I</button>
      </div>
      <div class="ctrl">
        <button class="chip zh-chip" id="zhBtn" title="只显示中文字体">中文<span class="n" id="zhN"></span></button>
      </div>
    </div>
    <div class="chips" id="chips"></div>
  </div>
</header>

<main>
  <div id="grid"></div>
  <div id="empty"><div class="big">&#128066;</div><div>没有找到匹配的字体</div></div>
</main>

<footer>
  页面使用本机已安装字体渲染，无需联网。共 <b id="total"></b> 款字体 · 生成于 __TODAY__ · 数据来源：本机字体目录
</footer>

<div id="modal" role="dialog" aria-modal="true" aria-label="字体预览">
  <div class="backdrop" id="mBackdrop"></div>
  <div class="panel">
    <button id="mClose" aria-label="关闭">&#10005;</button>
    <div id="mName"></div>
    <div id="mSample"></div>
    <div id="mMeta"></div>
  </div>
</div>

<script>
const FONTS = __FONTS_JSON__;
const CATS = __CATS_JSON__;
const DEF_SAMPLE = "The quick brown fox jumps over the lazy dog 0123456789\n天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。";

const grid = document.getElementById('grid');
const chipsEl = document.getElementById('chips');
const emptyEl = document.getElementById('empty');
const sampleInput = document.getElementById('sample');
sampleInput.value = DEF_SAMPLE;

const CAT_LABEL = {};
CATS.forEach(c => CAT_LABEL[c.key] = c.label);

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function famCss(name){
  return "'" + String(name).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'") + "', sans-serif";
}
function splitRows(s){
  const en = (s.match(/[A-Za-z]+[.,!?;:'’\-]*/g) || []).join(' ');
  const num = (s.match(/\d+/g) || []).join(' ');
  const zh = (s.match(/[\u3400-\u4dbf\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+/g) || []).join('');
  return [en, num, zh];
}

const state = {q:'', cat:'all', zh:false, size:32, weight:'400', italic:false};

const cards = FONTS.map(f => {
  const el = document.createElement('div');
  el.className = 'card';
  el.tabIndex = 0;
  el.setAttribute('role','button');
  el.dataset.name = (f.name + ' ' + (f.zh || '')).toLowerCase();
  el.dataset.file = (f.files && f.files[0] ? f.files[0].toLowerCase() : '');
  el.dataset.cat = f.cat;
  el.dataset.zh = (f.zh || /[\u4e00-\u9fff]/.test(f.name)) ? '1' : '0';
  el.innerHTML =
    '<div class="preview"><div class="sample"><div class="row"></div><div class="row"></div><div class="row"></div></div></div>' +
    '<div class="meta"><span class="names"><span class="name"></span><span class="en"></span></span><span class="tags">' +
    '<span class="tag"></span><span class="tag file"></span></span></div>';
  el.querySelector('.sample').style.fontFamily = famCss(f.name);
  el.querySelector('.name').textContent = f.zh || f.name;
  el.querySelector('.en').textContent = (f.zh && f.zh !== f.name) ? f.name : '';
  el.querySelector('.tag').textContent = CAT_LABEL[f.cat] || '其他';
  el.querySelector('.tag.file').textContent = f.files && f.files[0] ? f.files[0] : '—';
  el.addEventListener('click', () => openModal(f));
  el.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(f); }
  });
  grid.appendChild(el);
  return {f, el};
});

function text(){ return sampleInput.value || DEF_SAMPLE; }
function paint(){
  const rows = splitRows(text()), fs = state.size + 'px', w = state.weight, it = state.italic;
  for (const {el} of cards) {
    const smp = el.querySelector('.sample');
    for (let i = 0; i < 3; i++) {
      const r = smp.children[i];
      r.textContent = rows[i];
      r.classList.toggle('empty', !rows[i]);
      r.style.fontSize = fs;
      r.style.fontWeight = w;
      r.style.fontStyle = it ? 'italic' : 'normal';
    }
  }
}
function applyFilter(){
  let vis = 0;
  const q = state.q.trim().toLowerCase();
  for (const {f, el} of cards) {
    const hit = (!q || el.dataset.name.includes(q) || el.dataset.file.includes(q)) &&
      (state.cat === 'all' || f.cat === state.cat) &&
      (!state.zh || el.dataset.zh === '1');
    el.classList.toggle('hide', !hit);
    if (hit) vis++;
  }
  emptyEl.classList.toggle('show', vis === 0);
}
function renderChips(){
  const counts = {};
  cards.forEach(({f}) => counts[f.cat] = (counts[f.cat] || 0) + 1);
  chipsEl.innerHTML = '';
  const mk = (key, label) => {
    const b = document.createElement('button');
    b.className = 'chip' + (state.cat === key ? ' on' : '');
    b.innerHTML = esc(label) + (key !== 'all' ? ' <span class="n">' + counts[key] + '</span>' : '');
    b.addEventListener('click', () => { state.cat = key; renderChips(); applyFilter(); });
    chipsEl.appendChild(b);
  };
  mk('all', '全部');
  CATS.forEach(c => mk(c.key, c.label));
  const zhCount = cards.filter(c => c.el.dataset.zh === '1').length;
  document.getElementById('zhN').textContent = zhCount;
  document.getElementById('zhBtn').classList.toggle('on', state.zh);
}

document.getElementById('q').addEventListener('input', e => { state.q = e.target.value; applyFilter(); });
sampleInput.addEventListener('input', paint);
const sizeEl = document.getElementById('size');
sizeEl.addEventListener('input', e => {
  state.size = +e.target.value;
  document.getElementById('sizeVal').textContent = e.target.value;
  paint();
});
document.querySelectorAll('.seg button[data-w]').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.seg button[data-w]').forEach(x => x.classList.remove('on'));
  b.classList.add('on');
  state.weight = b.dataset.w;
  paint();
}));
document.getElementById('italicBtn').addEventListener('click', () => {
  state.italic = !state.italic;
  document.getElementById('italicBtn').classList.toggle('on', state.italic);
  paint();
});
document.getElementById('zhBtn').addEventListener('click', () => {
  state.zh = !state.zh;
  document.getElementById('zhBtn').classList.toggle('on', state.zh);
  applyFilter();
});

document.getElementById('sub').textContent = '共 ' + FONTS.length + ' 款字体 · 来自本机 Windows 字体目录';
document.getElementById('total').textContent = FONTS.length;

/* ---------- modal ---------- */
const modal = document.getElementById('modal');
function openModal(f){
  const disp = f.zh || f.name;
  document.getElementById('mName').innerHTML =
    '<span style="font-family:' + famCss(f.name) + '">' + esc(disp) + '</span>' +
    (disp !== f.name ? '<small>' + esc(f.name) + '</small>' : '') +
    '<small>' + esc(CAT_LABEL[f.cat] || '其他') + '</small>';
  const smp = document.getElementById('mSample');
  smp.innerHTML = '<div class="row"></div><div class="row"></div><div class="row"></div>';
  const rows = splitRows(text());
  for (let i = 0; i < 3; i++) {
    const r = smp.children[i];
    r.textContent = rows[i];
    r.classList.toggle('empty', !rows[i]);
  }
  smp.style.fontFamily = famCss(f.name);
  smp.style.fontSize = Math.min(56, state.size * 1.7) + 'px';
  smp.style.fontWeight = state.weight;
  smp.style.fontStyle = state.italic ? 'italic' : 'normal';
  let meta = '字体文件：<b>' + esc((f.files && f.files[0]) || '—') + '</b>';
  if (disp !== f.name) meta += ' · 英文名：<b>' + esc(f.name) + '</b>';
  meta += ' · 分类：<b>' + esc(CAT_LABEL[f.cat] || '其他') + '</b>';
  document.getElementById('mMeta').innerHTML = meta;
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closeModal(){ modal.classList.remove('show'); document.body.style.overflow = ''; }
document.getElementById('mClose').addEventListener('click', closeModal);
document.getElementById('mBackdrop').addEventListener('click', closeModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

renderChips();
paint();
applyFilter();
</script>
</body>
</html>
"""

    html = (
        TEMPLATE
        .replace("__FONTS_JSON__", fonts_json)
        .replace("__CATS_JSON__", cats_json)
        .replace("__TODAY__", today)
    )

    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} with {len(fonts)} fonts")
    print("Categories:", {c[0]: sum(1 for f in fonts if f['cat'] == c[0]) for c in CATS})


if __name__ == "__main__":
    main()
