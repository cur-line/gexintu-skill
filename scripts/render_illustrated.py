#!/usr/bin/env python3
"""Render/preview the seekable gexintu canvas template. Requires playwright + Chromium, ffmpeg.
Input: storyboard.json, build/timeline.json, project-local assets and voice file.
This renderer is for the existing canvas workflow, not a substitute for HyperFrames CLI checks.
"""
import argparse
import base64
import json
import mimetypes
from pathlib import Path
import subprocess
import time

MODES = {'battery', 'erase-send', 'queue', 'schedule', 'split-perception', 'reschedule',
         'chat-stop', 'listen-timer', 'calendar', 'timer-switch', 'choice-gallery', 'reply'}
LAYOUTS = {'editorial', 'cinematic', 'hook', 'split-perception'}

def load_project(project):
    spec = json.loads((project / 'storyboard.json').read_text())
    timeline = json.loads((project / 'build/timeline.json').read_text())
    timing = {s['id']: s for s in timeline['scenes']}
    if len(timing) != len(timeline['scenes']):
        raise ValueError('Duplicate timeline scene IDs')
    ids = [s['id'] for s in spec['scenes']]
    if len(set(ids)) != len(ids) or set(ids) != set(timing):
        raise ValueError('Storyboard scene IDs must match timeline exactly')
    for s in spec['scenes']:
        if s['mode'] not in MODES:
            raise ValueError('Unknown mode ' + s['mode'])
        s['layout'] = s.get('layout', 'editorial')
        if s['layout'] not in LAYOUTS:
            raise ValueError(f"{s['id']}: unknown layout {s['layout']}")
        visual = dict(s)
        s.update(timing[s['id']])
        s.update({k: v for k, v in visual.items() if k not in ('start', 'end', 'duration', 'words', 'narration')})
        text = ''.join(w['t'] for w in s['words'])
        cues = list(s['cues']) + ([s['image_after']['cue']] if 'image_after' in s else [])
        cues += [stage['cue'] for stage in s.get('title_after', [])]
        for cue in cues:
            if cue not in text:
                raise ValueError(f"{s['id']}: cue absent: {cue}")
        for w in s['words']:
            if not s['start'] <= w['s'] <= w['e'] <= s['end'] + .01:
                raise ValueError(f"{s['id']}: timestamp out of scene bounds")
        media = [s['image']] + s.get('gallery', [])
        if 'secondary' in s: media.append(s['secondary'])
        if 'image_after' in s: media.append(s['image_after']['asset'])
        for key in media:
            if key not in spec['assets']:
                raise ValueError(f"{s['id']}: asset absent: {key}")
    spec['scenes'].sort(key=lambda s: s['start'])
    if spec.get('require_layout_variety'):
        layouts = [s['layout'] for s in spec['scenes']]
        if len(set(layouts)) < 3:
            raise ValueError('This storyboard requires at least three layout families')
        if any(a == b for a, b in zip(layouts, layouts[1:])):
            raise ValueError('Consecutive scenes repeat the same layout')
    spec['total'] = timeline['total']
    voice = (project / spec['voice']).resolve()
    if not voice.is_relative_to(project) or not voice.is_file():
        raise ValueError('Voice must exist within project')
    for key, rel in spec['assets'].items():
        path = (project / rel).resolve()
        if not path.is_relative_to(project) or not path.is_file():
            raise ValueError('Asset must exist within project: ' + rel)
        mime = mimetypes.guess_type(path.name)[0] or 'image/png'
        spec['assets'][key] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()
    template = Path(__file__).resolve().parents[1] / 'assets/illustrated-motion.html'
    html = template.read_text().replace('/*__DATA__*/null', json.dumps(spec, ensure_ascii=False))
    page = project / 'build/illustrated.html'
    page.write_text(html)
    return page, spec, voice

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--preview', help='comma-separated absolute seconds')
    ap.add_argument('--audit', action='store_true')
    ap.add_argument('--render', type=Path)
    args = ap.parse_args()
    project = args.project.resolve()
    page, spec, voice = load_project(project)
    print(f"Validated {len(spec['scenes'])} scenes, {len(spec['assets'])} assets; {spec['total']:.2f}s", flush=True)
    if not (args.preview or args.audit or args.render): return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--force-color-profile=srgb', '--font-render-hinting=none'])
        pg = browser.new_page(viewport={'width':1080, 'height':1920}, device_scale_factor=1)
        errors=[]
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(page.as_uri())
        pg.wait_for_function('window.__ready === true', timeout=60000)
        if args.audit:
            result=pg.evaluate('''total=>{let violations=[];for(let t=0;t<total;t+=.25){window.renderAt(t);for(let b of window.__textAudit){if(b.x<65||b.x+b.w>1015||b.y<135||b.y+b.h>1810)violations.push({t,...b});}}return violations;}''', spec['total'])
            (project/'build/layout-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            if result or errors: raise RuntimeError(f'Layout/runtime audit failed: {result[:5]}, {errors}')
            print('Quarter-second text-bound audit passed. Visual overlaps still require inspection.',flush=True)
        if args.preview:
            dest=project/'build/previews';dest.mkdir(exist_ok=True)
            for t in map(float,args.preview.split(',')):
                pg.evaluate('t=>window.renderAt(t)',t)
                out=dest/f'{t:06.2f}.png'
                pg.screenshot(path=str(out))
                print(out,flush=True)
        if args.render:
            out=args.render.resolve();out.parent.mkdir(parents=True,exist_ok=True)
            if out.exists(): raise FileExistsError('Use a new versioned output: '+str(out))
            command=['ffmpeg','-v','error','-f','image2pipe','-framerate','30','-vcodec','mjpeg','-i','pipe:0','-i',str(voice),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-t',str(spec['total']),'-movflags','+faststart',str(out)]
            count=int(spec['total']*30)+1;t0=time.monotonic()
            with subprocess.Popen(command,stdin=subprocess.PIPE) as proc:
                try:
                    for i in range(count):
                        frame=pg.evaluate("t=>{window.renderAt(t);return document.querySelector('canvas').toDataURL('image/jpeg',.93).split(',')[1]}",i/30)
                        proc.stdin.write(base64.b64decode(frame))
                        if i and i%300==0: print(f'{i}/{count} frames; {time.monotonic()-t0:.0f}s',flush=True)
                finally: proc.stdin.close()
                if proc.wait()!=0: raise RuntimeError('ffmpeg failed')
            if errors: raise RuntimeError('Browser errors: '+repr(errors))
            print('Rendered '+str(out),flush=True)
        browser.close()

if __name__=='__main__': main()
