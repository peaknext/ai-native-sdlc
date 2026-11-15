# ai-native-sdlc

[English](#english) | [ภาษาไทย](#ภาษาไทย)

## English

A toolkit for AI-native software development: **the AI does the work, a person decides at each gate, and every stage leaves a file in git as evidence.**

Adapted from Anthropic's article [The AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook). This is an independent adaptation, not an official Anthropic document.

### What is in this repo

| File | What it is | Who it is for |
|---|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | The playbook, written in Thai: the six-stage loop, roles, approval gates, metrics, checklists and a glossary | People, whether or not they write code |
| [`.claude/skills/ai-native-sdlc/`](.claude/skills/ai-native-sdlc/SKILL.md) | A skill that lets Claude follow the playbook on its own, with document templates and scripts (written in English) | Claude, and anyone who wants the detail |

### The loop in brief

```
1 Plan      ->  intent.md        what we want, and why
2 Design    ->  spec.md          what exactly will be built
3 Build     ->  plan.md          how the code will change, then build it
4 Test      ->  test results     prove it before a person looks
5 Deploy    ->  PR + review      a person approves; the AI never approves its own work
6 Maintain  ->  incident record  which loops back as a new intent.md
```

### Getting started

**In this repo:** open it in Claude Code and say what you want in plain language, in any language. For example:

- "I want to build a booking app for a barbershop. Help me get started."
- "Set this repo up for working with AI."
- "Fix this bug: ..."
- "Where does each piece of work stand?"

**In another repo:** copy the `.claude/skills/ai-native-sdlc/` folder to the same location there, or ask Claude to package the skill as `ai-native-sdlc.skill` and click Save skill to install it in your Claude account.

**Scaffolding a repo** (Claude runs this for you when you ask it to set a repo up):

```bash
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <repo-folder>          # CLAUDE.md, intent/, REVIEW.md
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <repo-folder> --all    # plus hooks, subagents, evals, CI and monitoring bands
python .claude/skills/ai-native-sdlc/scripts/sdlc.py status <repo-folder>        # where every change stands
```

The script never overwrites an existing file.

---

## ภาษาไทย

ชุดเครื่องมือสำหรับพัฒนาซอฟต์แวร์แบบ AI-native: **AI เป็นคนลงมือ คนเป็นผู้ตัดสินใจที่ด่าน และทุกขั้นทิ้งไฟล์หลักฐานไว้ใน git**

เรียบเรียงจากบทความ [The AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook) ของ Anthropic เอกสารนี้เป็นการเรียบเรียงโดยอิสระ ไม่ใช่เอกสารทางการของ Anthropic

### มีอะไรในนี้

| ไฟล์ | คืออะไร | สำหรับใคร |
|---|---|---|
| [`PLAYBOOK.md`](PLAYBOOK.md) | คู่มือภาษาไทย อธิบายวงจร 6 ขั้น บทบาท ด่านอนุมัติ ตัวชี้วัด checklist และอภิธานศัพท์ | คนอ่าน ทั้งคนเขียนโค้ดและไม่เขียนโค้ด |
| [`.claude/skills/ai-native-sdlc/`](.claude/skills/ai-native-sdlc/SKILL.md) | สกิลที่ทำให้ Claude ทำงานตาม playbook ได้เอง พร้อมแม่แบบเอกสารและสคริปต์ (เขียนเป็นภาษาอังกฤษ) | Claude และคนที่อยากดูรายละเอียด |

### วงจรโดยย่อ

```
1 Plan      ->  intent.md        ต้องการอะไร เพราะอะไร
2 Design    ->  spec.md          จะสร้างอะไรกันแน่
3 Build     ->  plan.md          จะแก้โค้ดอย่างไร แล้วจึงสร้าง
4 Test      ->  ผลทดสอบ          พิสูจน์ก่อนให้คนดู
5 Deploy    ->  PR + รีวิว        คนอนุมัติ AI ไม่อนุมัติงานตัวเอง
6 Maintain  ->  บันทึกเหตุการณ์    ซึ่งวนกลับเป็น intent.md ใบใหม่
```

### เริ่มใช้

**ในโปรเจกต์นี้:** เปิดด้วย Claude Code แล้วบอกสิ่งที่ต้องการเป็นภาษาธรรมดา เช่น

- "อยากทำแอปจองคิวร้านตัดผม ช่วยเริ่มให้หน่อย"
- "ตั้งค่าโปรเจกต์นี้ให้พร้อมทำงานกับ AI"
- "แก้บั๊กนี้ให้หน่อย ..."
- "ตอนนี้งานถึงไหนแล้ว"

**ในโปรเจกต์อื่น:** คัดลอกโฟลเดอร์ `.claude/skills/ai-native-sdlc/` ไปไว้ที่ตำแหน่งเดียวกันในโปรเจกต์นั้น หรือขอให้ Claude แพ็กสกิลเป็นไฟล์ `ai-native-sdlc.skill` แล้วกด Save skill เพื่อติดตั้งเข้าบัญชี Claude ของคุณ

**ติดตั้งโครงสร้างให้โปรเจกต์** (Claude รันให้เองเมื่อขอให้ตั้งค่า)

```bash
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <โฟลเดอร์โปรเจกต์>          # CLAUDE.md, intent/, REVIEW.md
python .claude/skills/ai-native-sdlc/scripts/sdlc.py init <โฟลเดอร์โปรเจกต์> --all    # รวม hook, ผู้ช่วย, eval, CI, เกณฑ์เฝ้าระวัง
python .claude/skills/ai-native-sdlc/scripts/sdlc.py status <โฟลเดอร์โปรเจกต์>        # งานไหนอยู่ขั้นไหน
```

สคริปต์ไม่เขียนทับไฟล์ที่มีอยู่แล้ว
