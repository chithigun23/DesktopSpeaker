#!/usr/bin/env python3
"""Realistic board textures for the website CAD viewer (JLC 4-layer, ENIG, green mask, white silk).

Two modes:

  ~/Applications/kicad.AppImage python3.11 make_pcb_textures.py dump BOARD.kicad_pcb OUT.json
      (pcbnew) board outline, drills (pads and vias, plated or not), footprint list and the board box.
      NEVER run the AppImage with "python3": that opens the GUI.

  VENV/bin/python -I make_pcb_textures.py build BOARD.kicad_pcb DUMP.json OUTDIR [--px-top 4096] [--px 2048]
      (numpy, pillow, cairosvg) exports the copper, mask and silk layers as SVG with kicad-cli, rasterises them
      over the board box and composites, per side:
        OUTDIR/{top,bottom}_albedo.jpg   sRGB colour (+ top_albedo_2k.jpg for small screens): mask over copper/FR4, ENIG pads, silk, holes, FR4 edge
        OUTDIR/{top,bottom}_rmb.jpg      linear data: R = bump height, G = roughness, B = metalness
                                         (three.js reads roughness from G and metalness from B; bumpMap reads R)
        OUTDIR/textures.json             frame, box, sizes and source board for the viewer
      The images are laid out in the glTF frame of the repacked pcb glb: u = (x - x0) / w along +x (board x),
      v = (y - y0) / h along +z (board y grows down = glTF +z), image row 0 = board top edge (y0). The bottom
      images are NOT mirrored: same (u, v) as the top, so the viewer uses one UV set for both faces.

The wrapper ai-files/helpers/make_pcb_textures.sh runs both modes, the glb export and the repack.
"""
import json, os, re, subprocess, sys

MM = 1e-6  # pcbnew internal unit (nm) -> mm


def dump(board, out):
    import pcbnew
    b = pcbnew.LoadBoard(board)
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, True)

    def chain(c):
        return [[c.CPoint(k).x * MM, c.CPoint(k).y * MM] for k in range(c.PointCount())]
    outline = []
    for i in range(ps.OutlineCount()):
        outline.append({'outer': chain(ps.Outline(i)), 'holes': [chain(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]})
    holes, fps = [], []
    for fp in b.GetFootprints():
        fps.append({'ref': fp.GetReference(), 'x': fp.GetPosition().x * MM, 'y': fp.GetPosition().y * MM,
                    'side': 'B' if fp.IsFlipped() else 'F', 'models': len(list(fp.Models())),
                    'pads': len(list(fp.Pads()))})
        for p in fp.Pads():
            d = p.GetDrillSize()
            if d.x <= 0:
                continue
            holes.append({'x': p.GetPosition().x * MM, 'y': p.GetPosition().y * MM, 'dx': d.x * MM, 'dy': d.y * MM,
                          'oblong': p.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE,
                          'rot': p.GetOrientation().AsDegrees(),
                          'plated': p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH, 'ref': fp.GetReference(), 'kind': 'pad'})
    nv = 0
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            v = pcbnew.Cast_to_PCB_VIA(t) if hasattr(pcbnew, 'Cast_to_PCB_VIA') else t
            d = v.GetDrillValue()
            holes.append({'x': v.GetPosition().x * MM, 'y': v.GetPosition().y * MM, 'dx': d * MM, 'dy': d * MM,
                          'oblong': False, 'rot': 0, 'plated': True, 'kind': 'via'})
            nv += 1
    bb = b.GetBoardEdgesBoundingBox()
    box = [bb.GetX() * MM, bb.GetY() * MM, bb.GetWidth() * MM, bb.GetHeight() * MM]
    json.dump({'board': os.path.abspath(board), 'box_mm': box, 'outline': outline, 'holes': holes, 'vias': nv,
               'footprints': fps, 'thickness_mm': b.GetDesignSettings().GetBoardThickness() * MM}, open(out, 'w'))
    print('dump: %d outline(s), %d holes (%d vias), %d footprints, box %s' % (len(outline), len(holes), nv, len(fps), box))


# ---------------------------------------------------------------------------------------------------- build
K = os.path.expanduser('~/Applications/kicad.AppImage')
MASK_GREEN = (0x16, 0x5a, 0x34)        # JLC green, mask over bare FR4 (sRGB)
MASK_GREEN_CU = (0x2c, 0x7a, 0x45)     # same mask over copper: brighter, slightly yellower
ENIG = (0xd9, 0xb7, 0x6a)              # immersion gold, albedo (metallic)
FR4 = (0xc8, 0xb4, 0x82)               # bare laminate under no mask (seen at NPTH rims and slots)
SILK = (0xf2, 0xf2, 0xee)
HOLE = (0x14, 0x12, 0x10)


def raster_svg(svg_path, box, W, H, mirror=False):
    """coverage 0..1 of the black items of a KiCad B&W SVG, cropped to box (x, y, w, h mm), W x H px"""
    import cairosvg, numpy as np, io
    from PIL import Image
    s = open(svg_path).read()
    x, y, w, h = box
    s = re.sub(r'width="[^"]*mm" height="[^"]*mm" viewBox="[^"]*"',
               'width="%d" height="%d" viewBox="%.4f %.4f %.4f %.4f" preserveAspectRatio="none"' % (W, H, x, y, w, h), s, count=1)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=W, output_height=H)
    im = Image.open(io.BytesIO(png)).convert('LA')
    a = np.asarray(im, dtype=np.float32) / 255.0
    cov = a[..., 1] * (1.0 - a[..., 0])
    return cov


def build(board, dumpf, outdir, px_top=4096, px=2048):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    D = json.load(open(dumpf))
    os.makedirs(outdir, exist_ok=True)
    svgdir = os.path.join(os.path.dirname(os.path.abspath(dumpf)), 'svg')   # work files stay beside the dump, not in OUTDIR
    os.makedirs(svgdir, exist_ok=True)
    for L in ['F.Cu', 'B.Cu', 'F.Mask', 'B.Mask', 'F.SilkS', 'B.SilkS']:
        subprocess.run([K, 'kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--exclude-drawing-sheet',
                        '--black-and-white', '--drill-shape-opt', '0', '-l', L, '-o', os.path.join(svgdir, L + '.svg'), board],
                       check=True, stdout=subprocess.DEVNULL)
    pts = [q for o in D['outline'] for q in o['outer']]                 # the outline itself (the edge box adds the line width)
    x0, y0 = min(q[0] for q in pts), min(q[1] for q in pts)
    box = (round(x0, 4), round(y0, 4), round(max(q[0] for q in pts) - x0, 4), round(max(q[1] for q in pts) - y0, 4))
    meta = {'board': D['board'], 'box_mm': box, 'sides': {}}
    for side, W in (('top', px_top), ('bottom', px)):
        H = W
        sx, sy = W / box[2], H / box[3]
        P = lambda X, Y: ((X - box[0]) * sx, (Y - box[1]) * sy)
        pre = 'F' if side == 'top' else 'B'
        cu = raster_svg(os.path.join(svgdir, pre + '.Cu.svg'), box, W, H)
        mo = raster_svg(os.path.join(svgdir, pre + '.Mask.svg'), box, W, H)   # mask OPENINGS
        sk = raster_svg(os.path.join(svgdir, pre + '.SilkS.svg'), box, W, H)
        sk = sk * (1.0 - mo)                                                    # the fab clips silk off openings
        # board outline (inside = 1) and holes
        ol = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(ol)
        for o in D['outline']:
            d.polygon([tuple(2 * v for v in P(*q)) for q in o['outer']], fill=255)
            for hh in o['holes']:
                d.polygon([tuple(2 * v for v in P(*q)) for q in hh], fill=0)
        hl = Image.new('L', (W * 2, H * 2), 0)
        rg = Image.new('L', (W * 2, H * 2), 0)          # copper ring around plated holes (barrel lip)
        vl = Image.new('L', (W * 2, H * 2), 0)          # tented via holes: mask dips into the hole, no bare copper
        dh, dr, dv = ImageDraw.Draw(hl), ImageDraw.Draw(rg), ImageDraw.Draw(vl)
        import math
        for q in D['holes']:
            cx, cy = P(q['x'], q['y'])
            rx, ry = q['dx'] / 2 * sx, q['dy'] / 2 * sy
            if q['oblong'] and abs(q['dx'] - q['dy']) > 1e-3:
                # stadium: sample the outline
                a = math.radians(-q['rot'])
                L2, R = max(q['dx'], q['dy']) / 2, min(q['dx'], q['dy']) / 2
                hor = q['dx'] >= q['dy']
                pts = []
                for k in range(48):
                    t = 2 * math.pi * k / 48
                    ex, ey = R * math.cos(t), R * math.sin(t)
                    c = (L2 - R) * (1 if math.cos(t) >= 0 else -1)
                    ux, uy = (ex + c, ey) if hor else (ex, ey + c)
                    X = q['x'] + ux * math.cos(a) - uy * math.sin(a)
                    Y = q['y'] + ux * math.sin(a) + uy * math.cos(a)
                    pts.append(tuple(2 * v for v in P(X, Y)))
                dh.polygon(pts, fill=255)
            elif q['kind'] == 'via':
                dv.ellipse([2 * (cx - rx), 2 * (cy - ry), 2 * (cx + rx), 2 * (cy + ry)], fill=255)
            else:
                dh.ellipse([2 * (cx - rx), 2 * (cy - ry), 2 * (cx + rx), 2 * (cy + ry)], fill=255)
                if q['plated'] and q['kind'] == 'pad':
                    k = 0.12 * sx
                    dr.ellipse([2 * (cx - rx - k), 2 * (cy - ry - k), 2 * (cx + rx + k), 2 * (cy + ry + k)], fill=255)
        ol = np.asarray(ol.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0
        hole = np.asarray(hl.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0
        ring = np.asarray(rg.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0
        via = np.asarray(vl.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0
        via = via * (1 - mo)                              # an untented via (mask opening) shows its drill as a hole
        hole = np.maximum(hole, via * 0 + np.asarray(vl.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255.0 * mo)
        # colour composite (linear-ish blend in sRGB space is fine for these flat colours)
        C = lambda c: np.array(c, dtype=np.float32)[None, None, :] / 255.0
        cu3, mo3, sk3 = cu[..., None], mo[..., None], sk[..., None]
        # mask: brighter where copper lies under it; a soft glow (blur) mimics the mask's thickness over traces
        cu_soft = np.asarray(Image.fromarray((cu * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=max(1, W / 2048))), dtype=np.float32)[..., None] / 255.0
        mask_col = C(MASK_GREEN) * (1 - cu_soft) + C(MASK_GREEN_CU) * cu_soft
        # very fine low-amplitude noise so large mask areas are not perfectly flat
        rng = np.random.default_rng(7)
        noise = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
        noise = np.asarray(Image.fromarray(((noise * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32)[..., None] / 255.0 - 0.5
        mask_col = mask_col * (1 + 0.06 * noise)
        open_col = C(ENIG) * cu3 + C(FR4) * (1 - cu3)
        col = mask_col * (1 - mo3) + open_col * mo3
        ring3 = (ring * (1 - hole))[..., None]
        col = col * (1 - ring3) + C(ENIG) * ring3
        col = col * (1 - sk3) + C(SILK) * sk3
        col = col * (1 - hole[..., None]) + C(HOLE) * hole[..., None]
        col = col * (1 - 0.6 * via[..., None])          # dimple of the tented via
        col = col * ol[..., None] + C(FR4) * (1 - ol[..., None])
        # roughness / metalness / bump
        gold = np.clip(mo * cu + ring * (1 - hole), 0, 1) * (1 - sk)
        rough = 0.5 * (1 - mo) + (0.32 * gold + 0.75 * (mo - np.minimum(mo, gold)))   # satin mask, slightly rough ENIG, matt laminate
        rough = rough * (1 - sk) + 0.82 * sk
        rough = rough * (1 - hole) + 0.9 * hole
        rough = rough * ol + 0.8 * (1 - ol)
        rough = rough + 0.03 * noise[..., 0]
        metal = gold * ol * (1 - hole)
        bump = 0.25 + 0.30 * cu_soft[..., 0] * (1 - mo) + 0.35 * mo * cu + 0.25 * sk - 0.25 * hole - 0.2 * via
        bump = bump * ol
        rgb = (np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)
        rmb = (np.stack([np.clip(bump, 0, 1), np.clip(rough, 0.05, 1), np.clip(metal, 0, 1)], -1) * 255 + 0.5).astype(np.uint8)
        fa, fr = os.path.join(outdir, side + '_albedo.jpg'), os.path.join(outdir, side + '_rmb.jpg')
        Image.fromarray(rgb).save(fa, quality=90, subsampling=0, optimize=True)
        a2k = None
        if W > 2048:                                    # small screens / GPUs below 4096 px textures use this one
            a2k = os.path.join(outdir, side + '_albedo_2k.jpg')
            Image.fromarray(rgb).resize((2048, 2048), Image.LANCZOS).save(a2k, quality=90, subsampling=0, optimize=True)
        rmbW = min(W, px)
        Image.fromarray(rmb).resize((rmbW, rmbW), Image.LANCZOS).save(fr, quality=92, subsampling=0, optimize=True)
        meta['sides'][side] = {'albedo': os.path.basename(fa), 'rmb': os.path.basename(fr), 'px': [W, H], 'rmb_px': [rmbW, rmbW],
                               'px_per_mm': [round(sx, 2), round(sy, 2)], 'bytes': os.path.getsize(fa) + os.path.getsize(fr)}
        if a2k:
            meta['sides'][side]['albedo_2k'] = os.path.basename(a2k)
        print(side, W, H, 'px', meta['sides'][side])
    meta.update({'frame': 'u = (board_x - box.x) / box.w, v = (board_y - box.y) / box.h; image row 0 = v 0; bottom not mirrored',
                 'mask': 'green (JLC default; ORDER-NOTES leaves the colour to the owner)', 'silk': 'white', 'finish': 'ENIG',
                 'thickness_mm': D.get('thickness_mm'), 'holes': len(D['holes']), 'vias': D['vias']})
    return meta


if __name__ == '__main__':
    if sys.argv[1] == 'dump':
        dump(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'build':
        a = sys.argv[2:]
        kw = {}
        if '--px-top' in a:
            i = a.index('--px-top'); kw['px_top'] = int(a[i + 1]); del a[i:i + 2]
        if '--px' in a:
            i = a.index('--px'); kw['px'] = int(a[i + 1]); del a[i:i + 2]
        m = build(a[0], a[1], a[2], **kw)
        extra = json.loads(os.environ.get('TEX_EXTRA', '{}'))
        m.update(extra)
        json.dump(m, open(os.path.join(a[2], 'textures.json'), 'w'), indent=1)
    else:
        sys.exit(__doc__)
