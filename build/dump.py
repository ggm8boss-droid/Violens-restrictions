import struct, sys, zlib

def records(data, off, end, depth=0):
    while off < end:
        typ = data[off:off+4].decode('latin1')
        size = struct.unpack_from('<I', data, off+4)[0]
        if typ == 'GRUP':
            yield from records(data, off+24, off+size, depth+1)
            off += size
        else:
            flags, fid = struct.unpack_from('<II', data, off+8)
            body = data[off+24:off+24+size]
            if flags & 0x40000:
                body = zlib.decompress(body[4:])
            yield typ, fid, flags, body
            off += 24 + size

def subs(body):
    o = 0
    while o < len(body):
        t = body[o:o+4].decode('latin1'); s = struct.unpack_from('<H', body, o+4)[0]
        yield t, body[o+6:o+6+s]
        o += 6 + s

OPS = {0:'==',1:'!=',2:'>',3:'>=',4:'<',5:'<='}
def ctda(d):
    op = d[0]
    oper = OPS.get(op >> 5, '?'); fl = op & 0x1f
    comp = struct.unpack_from('<I', d, 4)[0]
    compf = struct.unpack_from('<f', d, 4)[0]
    func, = struct.unpack_from('<H', d, 8)
    p1, p2, runon, ref, p3 = struct.unpack_from('<IIIIi', d, 12)
    cv = ('GLOB %08X' % comp) if fl & 4 else ('%g' % compf)
    return 'func=%d p1=%08X p2=%08X %s %s%s runon=%d ref=%08X' % (func, p1, p2, oper, cv, ' OR' if fl & 1 else '', runon, ref)

def main():
    path = sys.argv[1]
    want = sys.argv[2:]
    data = open(path, 'rb').read()
    hsize = struct.unpack_from('<I', data, 4)[0]
    for typ, fid, flags, body in records(data, 24 + hsize, len(data)):
        if typ != 'IDLE': continue
        s = list(subs(body))
        edid = next((v[:-1].decode('latin1') for t, v in s if t == 'EDID'), '')
        if want and not any(w.lower() in edid.lower() or w.upper() == '%08X' % fid for w in want): continue
        print('IDLE %08X %s' % (fid, edid))
        for t, v in s:
            if t == 'CTDA': print('   CTDA', ctda(v))
            elif t == 'ANAM': print('   ANAM parent=%08X prev=%08X' % struct.unpack('<II', v))
            elif t in ('DNAM', 'ENAM', 'CIS1', 'CIS2'): print('  ', t, v.rstrip(b'\0').decode('latin1'))
            elif t == 'DATA': print('   DATA', v.hex())

if __name__=="__main__": main()
