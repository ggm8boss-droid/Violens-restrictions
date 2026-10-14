"""Make 'Vio Restrictions - Wide Target.esp' (ESL): wider melee hit cone + longer melee reach.
usage: python make_wide_target.py <out esp> [angle, default 55] [reach, default 170]
vanilla: fCombatHitConeAngle 35 (engine default), fCombatDistance 141 (Skyrim.esm)
"""
import struct, sys

out = sys.argv[1]
angle = float(sys.argv[2]) if len(sys.argv) > 2 else 55.0
reach = float(sys.argv[3]) if len(sys.argv) > 3 else 170.0

def sub(t, data): return t.encode() + struct.pack('<H', len(data)) + data

def record(typ, fid, body, flags=0):
    return typ.encode() + struct.pack('<IIIHHHH', len(body), flags, fid, 0, 0, 0x2C, 0) + body

def gmst(fid, edid, value):
    return record('GMST', fid, sub('EDID', edid.encode() + b'\0') + sub('DATA', struct.pack('<f', value)))

recs = [gmst(0x01000800, 'fCombatHitConeAngle', angle),   # new setting (engine-only, not in Skyrim.esm)
        gmst(0x00055640, 'fCombatDistance', reach)]       # override of Skyrim.esm record
data = b''.join(recs)
grup = b'GRUP' + struct.pack('<I4sIHHHH', 24 + len(data), b'GMST', 0, 0, 0, 0, 0) + data

hdr = (sub('HEDR', struct.pack('<fII', 1.7, len(recs) + 1, 0x801)) +
       sub('CNAM', b'VioRestrictions\0') +
       sub('SNAM', ('Melee hit cone %g deg (vanilla 35), melee reach %g (vanilla 141) '
                    'so killmoves trigger from a wider area.' % (angle, reach)).encode() + b'\0') +
       sub('MAST', b'Skyrim.esm\0') + sub('DATA', b'\0' * 8))
tes4 = record('TES4', 0, hdr, flags=0x200)
open(out, 'wb').write(tes4 + grup)
print('wrote', out, 'angle =', angle, 'reach =', reach)
