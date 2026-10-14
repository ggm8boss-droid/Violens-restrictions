# Violens-restrictions
Vio Restrictions  (built on "VioLens SE - Height Control.esp")
===============================================================

Install: copy the contents of "Data" into Skyrim's Data folder (or zip "Data"'s
contents and install with Vortex).

Requires: VioLens SE.esp, SkyUI + MCM Helper. Light (ESL-flagged) plugin.

What it does
- Configurable height-difference limit for VioLens killmoves.
- Restores VioLens stealth killmoves when KaputtVanillaKillmoves.esp is installed
  (Kaputt takes over VioLens' sneak-root records 00096800 / 00100F18; this plugin
  adds new sneaking roots and re-attaches the 10 weapon sneak branches to them).
- MCM toggles: ignore block (with health limit), sleeping/lying targets,
  paralyzed targets, sitting/leaning targets, seated stealth kills.
- Attack angle: wider "front" arc (default 30..330 instead of VioLens' 90..270) so
  half-turned enemies still get front killmoves; sneaking keeps 90..270 so stealth
  kills from the side still work; creatures can get front killmoves from any angle.
- Low health finisher (player only): killmove when the enemy is at or below X% health
  even if the hit isn't lethal (default on, 20%). Ignore-block is player-only too.
- Allow killmoves while the attacker is staggered (default on).
- Two-handed stealth killmoves (greatsword / battleaxe / warhammer): Throat Slit, Neck Break,
  Sleeper Hold or a random mix - VioLens has none for two-handers.
- The unarmed suplex (back killmove) follows the MCM height limits instead of a fixed +/-20.
- Back killmoves with a 1H axe / mace: VioLens' default (matched) back set has none for them,
  so they now use the axe/mace suplex from the mixed set instead of doing nothing.
- Advancing killmoves (VioLens setting) exposed as Off / Last enemy / On.
- Exposes VioLens' own globals: last-enemy-only, killmove chance,
  stealth chance, player immunity, vanilla killmove switch.

Optional: "Vio Restrictions - Wide Target.esp"
- Sets fCombatHitConeAngle to 82.5 (engine default 35): melee hits, and so killmoves,
  connect from a wider angle around the crosshair.
- Sets fCombatDistance to 255 (vanilla 141): about 80% longer melee reach.
- Both affect NPCs' melee too.
- Other values: python build\make_wide_target.py "<out esp>" <angle> <reach>

Rebuild (optional)
  build\build7.py <original height-only esp> <VioLens SE.esp> <out esp>
  (needs build\dump.py next to it)
