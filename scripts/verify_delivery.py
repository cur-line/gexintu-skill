#!/usr/bin/env python3
"""Verify exact delivery MP4 specs and full decode; does not assess artistic quality."""
import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def verify(path, max_seconds=180):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('Missing or empty video: ' + str(path))
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                            '-of', 'json', str(path)], check=True, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    videos = [s for s in data['streams'] if s['codec_type'] == 'video']
    audios = [s for s in data['streams'] if s['codec_type'] == 'audio']
    errors = []
    if len(videos) != 1 or not audios:
        errors.append('Expected one video stream and at least one audio stream')
    if videos:
        v = videos[0]
        if (v['codec_name'], v['width'], v['height']) != ('h264', 1080, 1920):
            errors.append('Expected H.264 at 1080x1920')
        if abs(float(Fraction(v['avg_frame_rate'])) - 30) > .01:
            errors.append('Expected 30 fps')
    if any(s['codec_name'] != 'aac' for s in audios):
        errors.append('Expected AAC audio')
    duration = float(data['format']['duration'])
    if not 0 < duration < max_seconds:
        errors.append(f'Duration {duration:.3f}s must be strictly below {max_seconds}s')
    if errors:
        raise ValueError('; '.join(errors))
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
                    '-map', '0:v', '-map', '0:a', '-f', 'null', '-'], check=True)
    return {'file': str(path), 'duration_seconds': duration, 'technical_check': 'PASS',
            'subjective_review': 'not assessed by this script'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('videos', nargs='+', type=Path)
    parser.add_argument('--max-seconds', type=float, default=180,
                        help='Strict upper bound; explicitly override for approved historical videos')
    args = parser.parse_args()
    failed = False
    for path in args.videos:
        try:
            print(json.dumps(verify(path.resolve(), args.max_seconds), ensure_ascii=False))
        except (ValueError, KeyError, subprocess.CalledProcessError, OSError) as exc:
            failed = True
            print(json.dumps({'file': str(path), 'technical_check': 'FAIL', 'error': str(exc)}, ensure_ascii=False))
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
