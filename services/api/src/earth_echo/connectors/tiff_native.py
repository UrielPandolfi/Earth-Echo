"""Independent classic-TIFF verification for the qualified Sentinel C1 COGs.

Only the first/full-resolution IFD, one unsigned band, DEFLATE and horizontal
predictor are supported. Fail closed on a changed encoding; never use overviews.
"""
import math
import struct
import zlib
import numpy as np


def native_window(source, window):
    if source.read_at(0,4)!=b'II*\x00':raise ValueError('Independent TIFF reader requires little-endian classic TIFF')
    offset=struct.unpack('<I',source.read_at(4,4))[0]
    count=struct.unpack('<H',source.read_at(offset,2))[0]
    if not 1<=count<=128:raise ValueError('Unexpected TIFF IFD budget')
    fields={}
    for i in range(count):
        tag,kind,n,inline=struct.unpack('<HHI4s',source.read_at(offset+2+12*i,12))
        formats={1:'B',2:'c',3:'H',4:'I',12:'d'}
        if kind not in formats or n>1_000_000:raise ValueError('Unsupported TIFF field encoding')
        fmt=formats[kind];length=struct.calcsize(fmt)*n
        raw=inline[:length] if length<=4 else source.read_at(struct.unpack('<I',inline)[0],length)
        fields[tag]=raw.rstrip(b'\x00').decode() if kind==2 else struct.unpack('<'+str(n)+fmt,raw)
    one=lambda tag,default=None:fields.get(tag,(default,))[0]
    width,height=one(256),one(257);bits=one(258)
    if bits not in (8,16) or one(259)!=8 or one(277)!=1 or one(339,1)!=1 or one(284,1)!=1 or one(274,1)!=1 or one(317,1) not in (1,2):
        raise ValueError('Independent TIFF reader: unexpected band/compression/predictor')
    tw,th=one(322),one(323)
    if not tw or not th or tw*th>1_048_576:raise ValueError('TIFF tile exceeds decoded budget')
    tiles_across=math.ceil(width/tw);tile_count=tiles_across*math.ceil(height/th)
    if len(fields[324])!=tile_count or len(fields[325])!=tile_count:raise ValueError('TIFF tile directory mismatch')
    c0,r0,w,h=map(int,window.flatten())
    if not (0<=c0<c0+w<=width and 0<=r0<r0+h<=height and 0<w*h<=2_000_000):raise ValueError('Independent TIFF window budget')
    dtype=np.dtype('<u2' if bits==16 else 'u1');result=np.empty((h,w),dtype=dtype)
    for ty in range(r0//th,(r0+h-1)//th+1):
        for tx in range(c0//tw,(c0+w-1)//tw+1):
            index=ty*tiles_across+tx;size=tw*th*dtype.itemsize
            codec=zlib.decompressobj();decoded=codec.decompress(source.read_at(fields[324][index],fields[325][index]),size+1)
            if len(decoded)!=size or not codec.eof or codec.unused_data:raise ValueError('TIFF DEFLATE length/stream mismatch')
            tile=np.frombuffer(decoded,dtype=dtype).reshape(th,tw)
            if one(317,1)==2:tile=np.cumsum(tile,axis=1,dtype=np.uint64).astype(dtype)
            x0,x1=max(c0,tx*tw),min(c0+w,(tx+1)*tw);y0,y1=max(r0,ty*th),min(r0+h,(ty+1)*th)
            result[y0-r0:y1-r0,x0-c0:x1-c0]=tile[y0-ty*th:y1-ty*th,x0-tx*tw:x1-tx*tw]
    return result,fields
