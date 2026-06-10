# RPG_Role — 復古 RPG 素材生成器 🎮

自動生成 DQ(勇者鬥惡龍)風格的復古像素遊戲素材:**角色、怪物、道具圖示、
大世界地圖、地下迷宮**,全部給定種子(seed)即可穩定重現。
角色與怪物附帶完整動作組:**待機、移動(四方向)、攻擊、絕招、施法、受傷、倒下**。

```bash
python3 -m rpg_role party --seed 1 --out out/ --gifs    # 六職業角色
python3 -m rpg_role horde --seed 1 --out out/ --gifs    # 全部怪物
python3 -m rpg_role items --out out/                     # 60 種道具圖示
python3 -m rpg_role map --kind overworld --seed 7       # 大世界地圖
python3 -m rpg_role map --kind dungeon --seed 7         # 地下迷宮
```

## 兩種畫風

| 風格 | 影格 | 來源 | 適合 |
|------|------|------|------|
| **lpc**(預設) | 64×64(武器揮擊 128/192) | [Universal LPC Spritesheet](https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator) 美術師手繪圖層合成 | 正式遊戲畫面 |
| **mini** | 32×32 | 純程式繪製(零素材依賴) | 雛型 / 小地圖 / 復古極簡風 |

LPC 素材已抽選 vendor 在 `assets/lpc/`(CC-BY-SA 3.0 / GPL 3.0,
發佈遊戲時需附 `assets/lpc/ATTRIBUTION.md` 的作者名單;本專案程式碼本身為 MIT)。

## 特色

- **6 種職業**:勇者 hero、戰士 warrior、魔法師 mage、僧侶 priest、盜賊 thief、武鬥家 monk
- **8 類怪物**:獸人 orc、哥布林 goblin、骷髏 skeleton、殭屍 zombie、狼人 wolfman、
  蜥蜴人 lizardman、牛頭人 minotaur(LPC 風格,與角色同動作組)+
  史萊姆 slime 六色(程序生成,經典彈跳動畫)
- **60 種道具圖示**(32×32 程序生成):武器/防具/藥水/卷軸/寶石/金幣/鑰匙/寶箱…
  輸出 atlas.png + atlas.json
- **地圖生成**:大世界(噪聲生成大陸、沙灘/森林/山脈/沼澤、城堡+城鎮+洞窟+道路)
  與地下迷宮(房間+走廊+樓梯+寶箱,保證全圖連通),輸出 map.png / map.json / tileset.png
- **程序化生成**:膚色、髮型、髮色、配色由 seed 決定,同一 seed 永遠生成同一隻角色
- **完整動作表**(每個動作 × 四方向):

  | 動作 | 影格數 | 用途 |
  |------|--------|------|
  | idle | 2 | 地圖/戰鬥待機 |
  | walk | 4 | 地圖移動 |
  | attack | 4 | 普通攻擊(含斬擊特效) |
  | special | 6 | 絕招(蓄力→大範圍斬擊→火花) |
  | cast | 4 | 施法(魔法陣+粒子) |
  | hurt | 2 | 受擊 |
  | dead | 1 | 倒下 |

- **遊戲引擎就緒**:輸出每動作的 sprite sheet PNG、總表 `spritesheet.png`、
  以及 `spritesheet.json` 中繼資料(影格大小、列序、fps 建議),可直接餵給
  Godot / Unity / Pygame / Phaser
- **GIF 預覽**:`--gifs` 會輸出每個動作的動畫預覽

## 安裝

```bash
pip install pillow
```

## 使用

```bash
cd RPG_Role

# 生成一隻角色(所有動作,預設 lpc 高精緻風格)
python3 -m rpg_role generate --job hero --seed 7 --out out/ --gifs

# 一次生成全部 6 職業
python3 -m rpg_role party --seed 1 --out out/ --gifs

# 32px 極簡程序風
python3 -m rpg_role party --seed 1 --out out/ --style mini --scale 2

# 列出職業
python3 -m rpg_role jobs
```

輸出結構:

```
out/hero_7_lpc/
  idle.png  walk.png  attack.png  special.png  cast.png  hurt.png  dead.png
  spritesheet.json   # 引擎用中繼資料(各動作影格大小、列序、fps)
  preview_*.gif      # 動畫預覽(--gifs)
```

sprite sheet 格式:每列一個方向(順序 down, left, right, up),每欄一個影格。
lpc 風格基本影格 64×64;攻擊/絕招因武器揮擊範圍使用 128 或 192 的影格
(實際大小記錄在 `spritesheet.json` 的每個動作裡)。mini 風格固定 32×32。

### 更新 / 擴充 LPC 素材

素材清單定義在 `rpg_role/lpc_manifest.py`(想換衣服顏色、武器、髮型就改這裡),
然後重新抽取:

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator /tmp/lpc
(cd /tmp/lpc && git sparse-checkout set spritesheets sheet_definitions sources)
python3 tools/vendor_lpc.py /tmp/lpc
```

## 程式生成原理

`rpg_role/` 不依賴任何圖庫素材,角色是純程式畫出來的:

1. `character.py` — 由 (job, seed) 決定膚色/髮型/配色/武器
2. `drawing.py` — 把身體部位(頭/髮/軀幹/手/腳/披風/武器)畫在 32×32 網格上,
   依姿勢參數(步伐、揮擊角度、特效影格)做逐格動畫
3. `canvas.py` — 自動上光影(頂部亮、底部暗)+ 1px 深色描邊,形成復古風格
4. `sheets.py` — 組裝 sprite sheet / GIF / JSON

## 測試

```bash
python3 tests/test_generator.py
```

## Roadmap

- [x] 高精緻圖源後端(LPC 開源像素素材庫)
- [x] 怪物生成器(LPC 人形怪 + 程序史萊姆)
- [x] 道具圖示生成器
- [x] 地圖生成器(大世界 + 迷宮)
- [ ] 女性角色基底 / 更多部件(披風、盾牌、更多武器)
- [ ] 大型 Boss 怪物(龍、巨人)
- [ ] 之後搭配故事專案組成完整遊戲
