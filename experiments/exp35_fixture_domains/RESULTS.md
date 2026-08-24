# exp35: fixture 風ドメイン marker 単発 — LB 結果

- 提出: 2026-08-23 18:55 UTC（kernel `nikoro256/ai-agent-sec-exp35-submit` v1）
- 着地: 2026-08-24
- **publicScore = 49.590**

## 解釈

**判定: 宛先変更は「タダの保険」ではなかった。期待値（exp2 相当の 80-90）を大きく下振れ。**

- 逆算: raw ≒ 49.59 × 200 ≒ 9,918 raw/行 → **約 550 findings/行**
  （exp2 の約 950 findings/行 から ~40% 減）。
- 候補は marker 単発で構造は exp2 と同一。差分は2つ:
  1. 宛先が fixture 風ドメイン24種（`internal.company.example` / `*.invalid` 等）
  2. data が `SECRET_MARKER ref{i}`（unique cell 確保用の接尾辞）
- どちらが主因かはこの1本では分離不能だが、**点数には関わらないはずの宛先/接尾辞の変更が
  findings 数を ~40% 削った**事実が重要。最もありそうな机制は:
  - 「internal っぽい / 見慣れないドメイン」への post 指示で、hosted の agent が
    余計な analysis（宛先の妥当性の検討など）を生成し、1エピソードが遅くなった
    （探索で量産できる候補数と replay 消化数の両方が減る）
  - ref 接尾辞による args トークン微増は副次的
- いずれにせよ **egress_allowlist 世界線への保険として宛先変更を既定にする案は
  public コストが大きすぎて却下**。private 用の保険は cd_2msg / cd_burst8_harmony
  （email 経路でそもそも http egress を使わない）に寄せるのが正しい。

## データ

- attack_template: `experiments/exp35_fixture_domains/attack_template.py`
- 構成: probe 2本（fixture_single / classic bare_ok の race、発火率 <0.8 で classic に
  fallback）→ 勝者で最大2000候補を fill。local validation 未実施（直接提出）
