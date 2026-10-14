# Killmove triggers — full audit (VioLens + Extension + Kaputt + Vio Restrictions)

Effective tree: 3,321 idle records, 2,589 animations. "Attacker" = you (or an NPC doing the killmove), "Target" = victim.
Controls: **VR** = Vio Restrictions MCM, **VL** = VioLens MCM, **—** = not controllable yet.

## A. Game engine (outside the plugins)
| # | Trigger | Control |
|---|---|---|
| A1 | The hit must be lethal (`ShouldAttackKill`) — damage ≥ remaining health | — (VR "Ignore block" only covers blocking) |
| A2 | Essential / protected NPCs never die, so A1 always fails | — |
| A3 | Target must be inside the melee hit cone and reach | VR Wide Target plugin (82.5° / 255) |
| A4 | Vanilla killmove switch (`KillMove` global) | VR |
| A5 | Only melee attacks from the normal / power attack idles; no mounted, no jump attacks | — |

## B. Main gate (4 VioLens roots: right / right power / left / left power)
| # | Trigger | Control |
|---|---|---|
| B1 | Height difference ±35 | VR |
| B2 | Weapon drawn, not mid-equip animation | — (required) |
| B3 | Not bow / crossbow in right hand | — (required) |
| B4 | Attacker not staggered | — |
| B5 | Attacker not mid-bash (attack state ≠ 6) | — |
| B6 | Target not already in a paired animation | — (required) |
| B7 | Target not leaning / lying | VR (furniture / sleeping) |
| B8 | Target not paralyzed | VR |
| B9 | Target not Astrid (quest) | — |
| B10 | Player immunity (NPCs can't killmove you) | VL / VR |
| B11 | Left-hand attacks only if `VL_HandActivation` = 1 (default **0** → left-hand attacks never killmove) | VL |
| B12 | Attacker not blocking (left-hand roots) | — |

## C. Direction (front / back)
| # | Trigger | Control |
|---|---|---|
| C1 | Front arc (VioLens 90–270) | VR (now 30–330) |
| C2 | Back killmoves: humanoid (ActorTypeNPC) targets only | — |
| C3 | Back killmoves: attacker not blocking | — |
| C4 | Creatures from behind | VR (any angle) |
| C5 | Back standing: attacker NOT sneaking; Back sneaking: attacker sneaking | — |
| C6 | Front: attacker not blocking unless holding a shield (shield-bash killmoves) | — |
| C7 | Target not sitting | VR / VL (stealth) |

## D. Chances & "last enemy"
| # | Trigger | Control |
|---|---|---|
| D1 | Killmove chance 100% (`VL_KillmoveChance`) | VL / VR |
| D2 | Dragon killmove chance 100% | VL |
| D3 | Stealth chance 100% | VL / VR |
| D4 | **Last enemy only** — front, back-standing killmoves | VL / VR |
| D5 | Advancing ("move") killmoves: Off by default; "Last enemy" mode | VL |
| D6 | Ranged (VATS) killmoves: last-enemy restriction ON by default | VL |

## E. Target type
| # | Trigger | Control |
|---|---|---|
| E1 | Humanoids (ActorTypeNPC) — full set | — |
| E2 | Creatures only if race is supported: bears, boars, chaurus hunters, death hounds/dogs, dragons, draugr, dwarven ballista & centurion, falmer, gargoyles, giants, hagravens, lurkers, rieklings, sabre cats, scribs/ash hoppers, ash spawn, spiders, spriggans, skeletons, trolls, wolves | — |
| E3 | **No killmoves at all** on unsupported creatures: skeevers, mudcrabs, horkers, mammoths, normal chaurus, dwarven spheres/spiders, atronachs, ice wraiths, wisps, dragon priests, netch, horses, deer/elk, goats… (no animations exist for their skeletons) | — |
| E4 | Dragons: target must be grounded / alive (health ≠ 0) | — |

## F. Weapon
| # | Trigger | Control |
|---|---|---|
| F1 | Right hand: fists, 1H sword/dagger/axe/mace, 2H greatsword/battleaxe/warhammer only — **staff, torch, spell in right hand = no killmove** | — |
| F2 | Left hand: empty, shield, spell, 1H (dual wield) variants | — |
| F3 | Stealth killmove per weapon is ONE chosen animation (dagger/unarmed/sword = neck break / throat slit…; axe/mace = 2) | VL (Stealth page) |
| F4 | Suplex: own ±20 height limit | — |

## G. Variant selectors (pick *which* animation, not *whether*)
Decapitation (perks Savage Strike / Devastating Blow, 40% chance, not essential, no `NoDecapitate`, not ghost),
bleed-out finishers, matched vs mixed sets (`VL_MeleeMode/NPCs/Creatures/BackKillmoves`), per-weapon animation
toggles (`VL_zRandomizer*`, `VL_zToggle*`), camera/perspective variants (`VL_Perspective`, `VL_1stPCheck`).
These choose between animations; if one variant fails, its siblings are tried.

## H. Mods in the chain
- KaputtVanillaKillmoves.esp: hijacked VioLens sneak roots (fixed by VR); Kaputt triggers are all disabled in kaputt.json.
- KillmoveParalysisFix.dll: fixes stuck-paralysis after killmoves; no gating.
