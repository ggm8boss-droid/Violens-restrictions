"""Build 'VioLens SE - Height Control.esp' v6.
usage: python build5.py <original height esp (.bak)> <VioLens SE.esp> <out esp>
- 4 VL roots: height + ignore block + sleeping + paralyzed + leaning options
- front / back-standing roots: sitting option
- restores VioLens stealth branch (Kaputt hijacks 00096800 / 00100F18): two new
  sneaking roots + re-parented weapon sneak roots
- front roots: configurable front arc (wider than VioLens' 90..270) when not sneaking,
  optional any-angle front killmoves on creatures (they have no back killmoves)
- lethal-hit bypass (player only): killmove when target health <= X% even if the hit isn't lethal;
  the ignore-block path is player-only too
- allow killmoves while the attacker is staggered
- two-handed stealth killmoves: copy of VioLens' sword stealth branch for greatsword / battleaxe / warhammer,
  animation choice in VLH_KillmoveStealth2H (same 1..7 options as VioLens)
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dump import records, subs

base_path, vl_path, out_path = sys.argv[1:4]

G_IGNORE_BLOCK, G_BLOCK_HP, G_SLEEP, G_PARALYZED, G_FURNITURE = 0x05000804, 0x05000805, 0x05000806, 0x05000807, 0x05000808
NEW_SNEAK00, NEW_SNEAK = 0x05000809, 0x0500080A
G_ARC_MIN, G_ARC_MAX, G_CREATURE_ANY = 0x0500080B, 0x0500080C, 0x0500080D
G_LOWHP, G_LOWHP_PCT, G_STAGGER = 0x0500080E, 0x0500080F, 0x05000810
G_STEALTH_2H = 0x0500083F
FIRST_2H_ID = 0x811                  # 2 x 20 copied records -> 0x811..0x838
NEXT_ID = 0x840
VL_STEALTH_SWORD = 0x04149F50

F_SHOULD_ATTACK_KILL, F_GET_GLOBAL, F_IS_BLOCKING, F_AV_PERCENT, F_FURN_ANIM, F_GET_AV = 678, 74, 569, 640, 613, 14
F_REL_ANGLE, F_HAS_KEYWORD, F_IS_SNEAKING, F_GET_IS_ID, F_IS_STAGGERED = 584, 560, 286, 72, 701
PLAYER = 0x00000007
KW_ACTOR_TYPE_NPC, AXIS_Z = 0x00013794, 0x5A
AV_HEALTH, AV_PARALYSIS = 24, 53
SIT, LAY, LEAN = 1, 2, 4
EQ, NE, GE, LE = 0, 1, 3, 5

def cond(func, op, value, p1=0, target=False, OR=False, glob=False, p2=0):
    flags = (1 if OR else 0) | (4 if glob else 0)
    comp = struct.pack('<I', value) if glob else struct.pack('<f', value)
    return b'CTDA' + struct.pack('<H', 32) + struct.pack('<B3s', (op << 5) | flags, b'\0\0\0') + comp + \
        struct.pack('<HHIIIIi', func, 0, p1, p2, 1 if target else 0, 0, -1)

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data

def split_subs(body):
    out, o = [], 0
    while o < len(body):
        s = struct.unpack_from('<H', body, o + 4)[0]
        out.append(body[o:o + 6 + s]); o += 6 + s
    return out

def parse_cond(raw):
    return (struct.unpack_from('<H', raw, 14)[0], struct.unpack_from('<I', raw, 18)[0],
            struct.unpack_from('<I', raw, 26)[0], raw[6] >> 5, raw[6] & 0x1F, struct.unpack_from('<f', raw, 10)[0])

def opt_out(raw, glob_id):
    """turn condition X (AND) into (X OR glob==1)"""
    return [raw[:6] + bytes([raw[6] | 1]) + raw[7:], cond(F_GET_GLOBAL, EQ, 1.0, p1=glob_id)]

def patch(body, edits):
    out, done = [], set()
    for raw in split_subs(body):
        if raw[:4] == b'CTDA':
            func, p1, runon, op, flags, val = parse_cond(raw)
            plain = not (flags & 1)
            if 'block' in edits and func == F_SHOULD_ATTACK_KILL and op == EQ and val == 1.0 and plain:
                # Kill OR (attacker is player AND (BlockPath OR LowHealthPath)), in CNF:
                # (Kill | Player) & for b in BlockPath, l in LowHealthPath: (Kill | b | l)
                kill = lambda: cond(F_SHOULD_ATTACK_KILL, EQ, 1.0, OR=True)
                out += [kill(), cond(F_GET_IS_ID, EQ, 1.0, p1=PLAYER)]
                block_path = (lambda: cond(F_GET_GLOBAL, EQ, 1.0, p1=G_IGNORE_BLOCK, OR=True),
                              lambda: cond(F_IS_BLOCKING, EQ, 1.0, target=True, OR=True),
                              lambda: cond(F_AV_PERCENT, LE, G_BLOCK_HP, p1=AV_HEALTH, target=True, glob=True, OR=True))
                low_path = (lambda: cond(F_GET_GLOBAL, EQ, 1.0, p1=G_LOWHP),
                            lambda: cond(F_AV_PERCENT, LE, G_LOWHP_PCT, p1=AV_HEALTH, target=True, glob=True))
                for b in block_path:
                    for l in low_path:
                        out += [kill(), b(), l()]
                done.add('block'); continue
            if 'stagger' in edits and func == F_IS_STAGGERED and op == NE and runon == 0 and plain:
                out += opt_out(raw, G_STAGGER); done.add('stagger'); continue
            if func == F_FURN_ANIM and runon == 1 and op == NE and plain:
                key = {LAY: 'sleep', LEAN: 'lean', SIT: 'sit'}.get(p1)
                if key in edits:
                    out += opt_out(raw, G_SLEEP if key == 'sleep' else G_FURNITURE); done.add(key); continue
            if 'angle' in edits and func == F_REL_ANGLE and plain and op in (GE, LE) and val in (90.0, 270.0):
                # in range = A(vanilla) OR (A(global) AND not sneaking) OR (target not NPC AND creature option)
                vanilla = lambda: cond(F_REL_ANGLE, op, val, p2=AXIS_Z, OR=True)
                wide = cond(F_REL_ANGLE, op, G_ARC_MIN if op == GE else G_ARC_MAX, p2=AXIS_Z, OR=True, glob=True)
                not_sneak = cond(F_IS_SNEAKING, NE, 1.0, OR=True)
                not_npc = cond(F_HAS_KEYWORD, NE, 1.0, p1=KW_ACTOR_TYPE_NPC, target=True)
                creature = cond(F_GET_GLOBAL, EQ, 1.0, p1=G_CREATURE_ANY)
                for a in (wide, not_sneak):
                    for b in (not_npc, creature):
                        out += [vanilla(), a, b]
                done.add('angle_lo' if op == GE else 'angle_hi'); continue
            if 'paralyzed' in edits and func == F_GET_AV and p1 == AV_PARALYSIS and runon == 1 and plain:
                out += opt_out(raw, G_PARALYZED); done.add('paralyzed'); continue
        out.append(raw)
    want = set(edits) - {'angle'} | ({'angle_lo', 'angle_hi'} if 'angle' in edits else set())
    assert done == want, (edits, done)
    return b''.join(out)

def set_sub(body, typ, data):
    return b''.join(sub(typ, data) if raw[:4] == typ.encode() else raw for raw in split_subs(body))

def record(typ, fid, body, flags=0):
    return typ.encode() + struct.pack('<IIIHHHH', len(body), flags, fid, 0, 0, 0x2C, 0) + body

def group(label, recs):
    data = b''.join(recs)
    return b'GRUP' + struct.pack('<I4sIHHHH', 24 + len(data), label.encode(), 0, 0, 0, 0, 0) + data

def glob(fid, edid, value):
    return record('GLOB', fid, sub('EDID', edid.encode() + b'\0') + sub('FNAM', b'f') + sub('FLTV', struct.pack('<f', value)))

def load(path):
    d = open(path, 'rb').read(); h = struct.unpack_from('<I', d, 4)[0]
    return d, h, {(t, f): (fl, b) for t, f, fl, b in records(d, 24 + h, len(d))}

def masters(d, h): return [v[:-1].decode().lower() for t, v in subs(d[24:24 + h]) if t == 'MAST']

base, bh, base_recs = load(base_path)
vl, vh, vl_recs = load(vl_path)
assert masters(base, bh)[:4] == masters(vl, vh) and masters(base, bh)[4] == 'violens se.esp'
assert not any(fl & 0x40000 for fl, _ in list(base_recs.values()) + list(vl_recs.values()))

globs = [record('GLOB', f, b, fl) for (t, f), (fl, b) in sorted(base_recs.items()) if t == 'GLOB']
globs += [glob(G_IGNORE_BLOCK, 'VLH_IgnoreBlockEnabled', 1.0),
          glob(G_BLOCK_HP, 'VLH_IgnoreBlockHealthPct', 0.25),
          glob(G_SLEEP, 'VLH_AllowSleepingEnabled', 1.0),
          glob(G_PARALYZED, 'VLH_AllowParalyzedEnabled', 0.0),
          glob(G_FURNITURE, 'VLH_AllowFurnitureEnabled', 0.0),
          glob(G_ARC_MIN, 'VLH_FrontArcMin', 30.0),
          glob(G_ARC_MAX, 'VLH_FrontArcMax', 330.0),
          glob(G_CREATURE_ANY, 'VLH_CreatureAnyAngle', 1.0),
          glob(G_LOWHP, 'VLH_LowHealthEnabled', 1.0),
          glob(G_LOWHP_PCT, 'VLH_LowHealthPct', 0.20),
          glob(G_STAGGER, 'VLH_AllowStaggered', 1.0),
          glob(G_STEALTH_2H, 'VLH_KillmoveStealth2H', 7.0)]
qusts = [record('QUST', f, b, fl) for (t, f), (fl, b) in sorted(base_recs.items()) if t == 'QUST']

idles = []
# 1) the four VL roots (already carry the height-check edits in the base plugin)
for (t, f), (fl, b) in sorted(base_recs.items()):
    if t == 'IDLE':
        idles.append(record('IDLE', f, patch(b, {'block', 'sleep', 'lean', 'paralyzed', 'stagger'}), fl))
# 2) front roots: sitting option + front arc; back-standing roots: sitting option
for f in (0x00100E8B, 0x00024CD4, 0x0408E4C9, 0x0408E5B8):
    fl, b = vl_recs[('IDLE', f)]
    idles.append(record('IDLE', f, patch(b, {'sit', 'angle'}), fl))
for f in (0x00100F16, 0x000E8458, 0x0408E5AD, 0x0408E69C):
    fl, b = vl_recs[('IDLE', f)]
    idles.append(record('IDLE', f, patch(b, {'sit'}), fl))
# 3) new sneaking roots = VioLens' original sneaking roots, placed after the back-standing roots
for new, orig, parent, prev, edid in ((NEW_SNEAK00, 0x00100F18, 0x042B7363, 0x00100F16, 'VLH_KillmovesBackSneakingRoot00'),
                                      (NEW_SNEAK, 0x00096800, 0x042B7365, 0x000E8458, 'VLH_KillmovesBackSneakingRoot')):
    fl, b = vl_recs[('IDLE', orig)]
    b = set_sub(b, 'EDID', edid.encode() + b'\0')
    b = set_sub(b, 'ANAM', struct.pack('<II', parent, prev))
    idles.append(record('IDLE', new, b, fl & ~0x200))
# 4) re-parent VioLens' weapon sneak roots onto the new nodes
moved = 0
for (t, f), (fl, b) in sorted(vl_recs.items()):
    if t != 'IDLE': continue
    an = dict(subs(b)).get('ANAM', b'')
    if len(an) != 8: continue
    par, prev = struct.unpack('<II', an)
    if par in (0x00100F18, 0x00096800):
        newpar = NEW_SNEAK00 if par == 0x00100F18 else NEW_SNEAK
        idles.append(record('IDLE', f, set_sub(b, 'ANAM', struct.pack('<II', newpar, prev)), fl)); moved += 1
assert moved == 10, moved

# 5) two-handed stealth branch: copy each sword stealth subtree, append after the mace root
def vl_children(parent):
    out = []
    for (t, f), (fl, b) in vl_recs.items():
        if t != 'IDLE': continue
        an = dict(subs(b)).get('ANAM', b'')
        if len(an) == 8 and struct.unpack('<I', an[:4])[0] == parent:
            out.append(f)
    return out

def retarget_glob(body, old, new):
    out = []
    for raw in split_subs(body):
        if raw[:4] == b'CTDA' and parse_cond(raw)[0] == F_GET_GLOBAL and parse_cond(raw)[1] == old:
            raw = raw[:18] + struct.pack('<I', new) + raw[22:]
        out.append(raw)
    return b''.join(out)

next_2h = FIRST_2H_ID
for sword_root, new_parent, last_sibling in ((0x04149F5A, NEW_SNEAK00, 0x04149F82), (0x01000819, NEW_SNEAK, 0x0414F0DE)):
    subtree, todo = [sword_root], [sword_root]
    while todo:
        kids_ = vl_children(todo.pop()); subtree += kids_; todo += kids_
    new_id = {}
    for f in subtree:
        new_id[f] = 0x05000000 | next_2h; next_2h += 1
    for f in subtree:
        fl, b = vl_recs[('IDLE', f)]
        par, prev = struct.unpack('<II', dict(subs(b))['ANAM'])
        edid = dict(subs(b))['EDID'][:-1].decode()
        edid = edid.replace('VL_KillMoveSneakSwordRoot', 'VLH_KillmoveSneak2HRoot')
        edid = edid.replace('VL_KillmoveSneakSwordRoot', 'VLH_KillmoveSneak2HRoot').replace('VL_Sword', 'VLH_2H')
        b = set_sub(b, 'EDID', edid.encode() + bytes(1))
        if f == sword_root:
            par, prev = new_parent, last_sibling
            body = [raw for raw in split_subs(b) if raw[:4] != b'CTDA']
            two_handed = cond(597, EQ, 5.0, p1=1, OR=True) + cond(597, EQ, 6.0, p1=1)
            b = body[0] + two_handed + b''.join(body[1:])      # EDID first, then conditions
        else:
            par, prev = new_id[par], new_id.get(prev, 0)
        b = set_sub(b, 'ANAM', struct.pack('<II', par, prev))
        b = retarget_glob(b, VL_STEALTH_SWORD, G_STEALTH_2H)
        idles.append(record('IDLE', new_id[f], b, fl & ~0x200))
assert next_2h <= 0x83F, hex(next_2h)

hdr = base[:24 + bh]
nrec = len(globs) + len(qusts) + len(idles) + 3
hsubs = []
for raw in split_subs(hdr[24:]):
    if raw[:4] == b'HEDR':
        ver = struct.unpack_from('<f', raw, 6)[0]
        raw = sub('HEDR', struct.pack('<fII', ver, nrec, NEXT_ID))
    hsubs.append(raw)
hbody = b''.join(hsubs)
header = hdr[:4] + struct.pack('<I', len(hbody)) + hdr[8:24] + hbody
open(out_path, 'wb').write(header + group('GLOB', globs) + group('QUST', qusts) + group('IDLE', idles))
print('wrote', out_path, '|', len(idles), 'idles,', len(globs), 'globals,', nrec, 'records+groups')
