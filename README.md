# ai-native-sdlc

ชุดเครื่องมือสำหรับพัฒนาซอฟต์แวร์แบบ AI-native: **AI เป็นคนลงมือ คนเป็นผู้ตัดสินใจที่ด่าน และทุกขั้นทิ้งไฟล์หลักฐานไว้ใน git**

เรียบเรียงจากบทความ [The AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) ของ Anthropic

## มีอะไรในนี้

| ไฟล์ | คืออะไร | สำหรับใคร |
|---|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | คู่มือภาษาไทย อธิบายวงจร 6 ขั้น บทบาท ด่านอนุมัติ ตัวชี้วัด checklist และอภิธานศัพท์ | คนอ่าน ทั้งคนเขียนโค้ดและไม่เขียนโค้ด |
| [`.claude/skills/ai-native-sdlc/`](.claude/skills/ai-native-sdlc/SKILL.md) | สกิลที่ทำให้ Claude ทำงานตาม playbook ได้เอง พร้อมแม่แบบเอกสารและสคริปต์ | Claude (และคนที่อยากดูรายละเอียด) |

## วงจรโดยย่อ

```
1 Plan      ->  intent.md   ต้องการอะไร เพราะอะไร
2 Design    ->  spec.md     จะสร้างอะไรกันแน่
3 Build     ->  plan.md     จะแก้โค้ดอย่างไร แล้วจึงสร้าง
4 Test      ->  ผลทดสอบ     พิสูจน์ก่อนให้คนดู
5 Deploy    ->  PR + รีวิว   คนอนุมัติ AI ไม่อนุมัติงานตัวเอง
6 Maintain  ->  บันทึกเหตุการณ์ ซึ่งวนกลับเป็น intent.md ใบใหม่
```

## เริ่มใช้

**ในโปรเจกต์นี้:** เปิดด้วย Claude Code แล้วบอกสิ่งที่ต้องการเป็นภาษาธรรมดา เช่น

- "อยากทำแอปจองคิวร้านตัดผม ช่วยเริ่มให้หน่อย"
- "ตั้งค่าโปรเจกต์นี้ให้พร้อมทำงานกับ AI"
- "แก้บั๊กนี้ให้หน่อย ..."
- "ตอนนี้งานถึงไหนแล้ว"

**ในโปรเจกต์อื่น:** คัดลอกโฟลเดอร์ `.claude/skills/ai-native-sdlc/` ไปไว้ที่ตำแหน่งเดียวกันในโปรเจกต์นั้น หรือติดตั้งไฟล์ `ai-native-sdlc.skill` เข้าบัญชี Claude ของคุณ

**ติดตั้งโครงสร้างให้โปรเจกต์** (Claude รันให้เองเมื่อขอให้ตั้งค่า)

```bash
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <โฟลเดอร์โปรเจกต์>          # CLAUDE.md, intent/, REVIEW.md
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <โฟลเดอร์โปรเจกต์> --all    # รวม hook, ผู้ช่วย, eval, CI, เกณฑ์เฝ้าระวัง
python .claude/skills/ai-native-sdlc/scripts/sdlc.py status <โฟลเดอร์โปรเจกต์>        # งานไหนอยู่ขั้นไหน
```

สคริปต์ไม่เขียนทับไฟล์ที่มีอยู่แล้ว
