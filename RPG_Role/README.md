# RPG_Role — 復古 RPG 角色點陣圖生成器 🎮

自動生成 DQ(勇者鬥惡龍)風格的復古像素角色,每個角色附帶完整動作組:
**待機、移動(四方向)、攻擊、絕招、施法、受傷、倒下**。
不需要美術功底 — 給定職業 + 種子(seed)就能穩定重現同一隻角色。

## 兩種畫風

| 風格 | 影格 | 來源 | 適合 |
|------|------|------|------|
| **lpc**(預設) | 64×64(武器揮擊 128/192) | [Universal LPC Spritesheet](https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator) 美術師手繪圖層合成 | 正式遊戲畫面 |
| **mini** | 32×32 | 純程式繪製(零素材依賴) | 雛型 / 小地圖 / 復古極簡風 |

LPC 素材已抽選 vendor 在 `assets/lpc/`(CC-BY-SA 3.0 / GPL 3.0,
發佈遊戲時需附 `assets/lpc/ATTRIBUTION.md` 的作者名單;本專案程式碼本身為 MIT)。

## 特色

- **6 種職業**:勇者 hero、戰士 warrior、魔法師 mage、僧侶 priest、盜賊 thief、武鬥家 monk
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

- [ ] 更精緻的圖源後端(整合開源像素素材庫,如 LPC)
- [ ] 怪物生成器
- [ ] 地圖 tile 生成器
- [ ] 之後搭配故事專案組成完整遊戲
