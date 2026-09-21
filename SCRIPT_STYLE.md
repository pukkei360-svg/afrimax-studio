# Script & Style Guide — Channel Formula

The two constants in every video:

1. **VISUAL: 3D animated style** — Pixar/Blender-quality render, cinematic
   lighting, 9:16 vertical. That never changes.
2. **PURPOSE: a moral** — every story ends with one spoken line of wisdom.

Everything else is a new world every time:

## Rotate settings & heroes (never repeat a formula)

| Story type | World | Hero | Moral direction (example) |
|------------|-------|------|---------------------------|
| King story | Palace, throne room, royal gardens | Young impatient king | Power listens before it commands |
| Boy story | Small town, school, riverside | Curious poor boy | Small kindness, big returns |
| Manager story | Modern office tower, glass city | Ruthless manager | People are not resources |
| Servant story | Old mansion, wealthy estate | Humble loyal servant | Trust is earned in silence |
| Farmer story | Village fields, seasons | Weathered farmer | Patience grows what force cannot |
| Fisherman story | African river at dawn (done) | Honest old fisherman | Honesty planted today becomes tomorrow's harvest |
| Warrior story | Ancient kingdom, battlefield | Proud general | Courage without wisdom is chaos |
| Merchant story | Bazaar, trade routes | Greedy trader | Fair scales weigh the soul |

## What stays identical every video

- **3D render style**: cinematic stills, volumetric light, warm grade, DOF
- **American-style script** (below)
- **Voice**: `en-US-AndrewMultilingualNeural`, rate `-10%`, pitch `-2Hz`
- **Cut**: NO intro title text, NO moral end card — hook opens on visuals,
  moral is SPOKEN over the final scene, slow fade to black
- **Audio**: music auto-ducks under narration, master -14 LUFS

## Script style (American YouTube storyteller)

1. **Cold-open hook in first 5 seconds** — a question or impossible situation:
   "What would you do if you found a bag full of gold... and no one was watching?"
2. **Direct address** — talk TO the viewer ("you"), never lecture.
3. **Short punchy sentences.** Fragments are fine. For drama.
4. **Present tense for action**, past only for backstory.
5. **Escalation beats**: setup → temptation → choice → climax → payoff.
6. **One-line moral, spoken plainly** at the end.
7. **Contrast + specifics**: numbers ("ten boats"), names ("Mama Zainab"),
   sensory verbs ("the drums began to beat").
8. **Pauses**: use "..." where the narrator should breathe.

## Writing a new story (story.json template)

Copy `story.json`, keep meta flags as-is, replace:
- `scenes[].keyframe_prompt` / `motion_prompt`: describe the new world,
  hero, wardrobe; always include "3D animated short film, Pixar-quality
  render" and one consistent character description repeated verbatim
- `scenes[].narration`: the American-style script lines
- Keep each scene's VO under ~12s (pad 1.2-1.4s)

Example openers by world:
- King: "Every king hears a thousand voices... but only one tells the truth."
- Manager: "He had four hundred people under him. And not one friend."
- Servant: "For thirty years, he guarded a secret worth more than his life."
