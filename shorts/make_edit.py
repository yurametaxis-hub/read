#!/usr/bin/env python3
"""Vertical edit of horizontal footage without a facecam: gameplay, trailers, fan concepts.

The footage sits in the middle (1080 x fg_h), a blurred copy fills the rest, the title plaque
rides on its top edge, short text beats pop up, slowed segments can get a zoom and a low boom.

    python3 shorts/make_edit.py shorts/jobs/concept_fight.json

Job keys (segment times are seconds of the SOURCE, text times are seconds of the OUTPUT):
  source, out        required
  segments           [{"start": 55.3, "end": 60.9, "x": 0.5, "y": 0.5, "zoom": 1.0, "speed": 1.0,
                       "boom": 71.1, "whoosh": true}, ...] played in this order;
                     x and y are the crop centre as a share of the source frame,
                     x_end makes the crop glide from x to x_end over the segment,
                     boom is the source time of an impact, whoosh plays on the cut into the segment
  fg_h, fg_y         footage height and its top edge in the 1080x1920 frame, default 1240 and 340
  title, title_sub   plaque on the top edge of the footage, *word* gets the accent colour
  texts              [{"text": "WAIT FOR IT...", "start": 0, "end": 2.5, "y": 1440, "size": 72}]
  grade              a little more contrast, colour and sharpness, default true
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_short import H, W, probe, render_title, sh  # noqa: E402

SR = 48000


def make_sfx(work):
    boom, whoosh = work / "boom.wav", work / "whoosh.wav"
    if not boom.exists():
        # sub drop with overdrive harmonics, so phone speakers that cut the lows still play it,
        # plus a short noise crack for the attack
        drop, body, crack = (work / f"boom_{p}.wav" for p in ("drop", "body", "crack"))
        sh(["sox", "-n", "-r", SR, "-c", "2", drop, "synth", "1.3", "sine", "150/35",
            "fade", "q", "0.003", "1.3", "1.1", "overdrive", "10", "lowpass", "1500", "gain", "-3"])
        sh(["sox", "-n", "-r", SR, "-c", "2", body, "synth", "0.3", "sine", "340/120",
            "fade", "q", "0.002", "0.3", "0.27", "overdrive", "8", "gain", "-4"])
        sh(["sox", "-n", "-r", SR, "-c", "2", crack, "synth", "0.15", "brownnoise",
            "fade", "q", "0.001", "0.15", "0.14", "lowpass", "3500", "gain", "4"])
        sh(["sox", "-m", drop, body, crack, boom, "gain", "-n", "-3"])
    if not whoosh.exists():  # short swell of filtered noise
        sh(["sox", "-n", "-r", SR, "-c", "2", whoosh, "synth", "0.55", "pinknoise",
            "fade", "q", "0.3", "0.55", "0.25", "highpass", "500", "lowpass", "5000", "gain", "-9"])
    return boom, whoosh


def crop_box(sw, sh_, fg_h, x, y, zoom):
    aspect = W / fg_h
    ch = sh_ / zoom
    cw = ch * aspect
    if cw > sw / zoom:
        cw = sw / zoom
        ch = cw / aspect
    cw, ch = int(cw) // 2 * 2, int(ch) // 2 * 2
    cx = min(max(x * sw - cw / 2, 0), sw - cw)
    cy = min(max(y * sh_ - ch / 2, 0), sh_ - ch)
    return cw, ch, int(cx), int(cy)


def build_texts(texts, path):
    import pysubs2
    subs = pysubs2.SSAFile()
    subs.info.update({"PlayResX": str(W), "PlayResY": str(H), "WrapStyle": "0", "ScaledBorderAndShadow": "yes"})
    subs.styles["Beat"] = pysubs2.SSAStyle(
        fontname="Montserrat Black", fontsize=72, primarycolor=pysubs2.Color(255, 255, 255),
        outlinecolor=pysubs2.Color(0, 0, 0), backcolor=pysubs2.Color(0, 0, 0, 110),
        outline=7, shadow=4, alignment=pysubs2.Alignment.MIDDLE_CENTER)
    for t in texts:
        tag = (f"{{\\pos(540,{t.get('y', 1440)})\\fs{t.get('size', 72)}\\fad(0,150)"
               f"\\fscx80\\fscy80\\t(0,120,\\fscx100\\fscy100)}}")
        subs.append(pysubs2.SSAEvent(start=int(t["start"] * 1000), end=int(t["end"] * 1000),
                                     style="Beat", text=tag + t["text"]))
    subs.save(str(path))


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    src, out = job["source"], Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_suffix("")
    sw, sh_, fps = probe(src)
    fps = min(round(fps), 60)
    fg_h, fg_y = int(job.get("fg_h", 1240)), int(job.get("fg_y", 340))
    segs = job["segments"]
    n = len(segs)

    seg_inputs, vparts, aparts, booms, whooshes, t = [], [], [], [], [], 0.0
    for i, s in enumerate(segs):
        a, b = float(s["start"]), float(s["end"])
        sp, z = float(s.get("speed", 1.0)), float(s.get("zoom", 1.0))
        seg_inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src]
        cw, ch, cx, cy = crop_box(sw, sh_, fg_h, s.get("x", 0.5), s.get("y", 0.5), z)
        xexpr = str(cx)
        if s.get("x_end") is not None:  # smooth pan to follow a subject that drifts sideways
            cx2 = crop_box(sw, sh_, fg_h, s["x_end"], s.get("y", 0.5), z)[2]
            xexpr = f"'{cx}+({cx2}-{cx})*(0.5-0.5*cos(PI*min(t/{b - a:.3f},1)))'"
        v = f"[{i}:v]setpts=PTS-STARTPTS,crop={cw}:{ch}:{xexpr}:{cy},scale={W}:{fg_h}:flags=lanczos,setsar=1"
        if sp != 1:
            v += f",setpts=PTS/{sp}"
        vparts.append(v + f",fps={fps}[v{i}]")
        au = f"[{i}:a]asetpts=PTS-STARTPTS,aresample={SR}"
        if sp < 1:
            au += f",asetrate={int(SR * sp)},aresample={SR}"
        elif sp > 1:
            au += f",atempo={sp}"
        aparts.append(au + f"[a{i}]")
        if s.get("boom") is not None:
            booms.append(t + (float(s["boom"]) - a) / sp)
        if s.get("whoosh") and i > 0:
            whooshes.append(max(t - 0.3, 0.0))
        t += (b - a) / sp
    dur = round(t, 3)

    # pass 1: audio with sound effects, then measure loudness
    boom_wav, whoosh_wav = make_sfx(out.parent)
    ag = aparts + ["".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[amain]"]
    mix = ["[amain]"]
    for k, (wav_idx, times, tag) in enumerate([(n, booms, "b"), (n + 1, whooshes, "w")]):
        if times:
            ag.append(f"[{wav_idx}:a]asplit={len(times)}" + "".join(f"[{tag}{j}s]" for j in range(len(times))))
            for j, tt in enumerate(times):
                ms = int(tt * 1000)
                ag.append(f"[{tag}{j}s]adelay={ms}|{ms}[{tag}{j}]")
                mix.append(f"[{tag}{j}]")
    ag.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first[aout]")
    mix_wav = Path(str(work) + ".mix.wav")
    sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *seg_inputs, "-i", boom_wav, "-i", whoosh_wav,
        "-filter_complex", ";".join(ag), "-map", "[aout]", "-t", dur, mix_wav])
    meas = sh(["ffmpeg", "-hide_banner", "-i", mix_wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
               "-f", "null", "-"], capture=True)
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    loud = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
            f":linear=true,aresample={SR}")

    # pass 2: picture
    grade = "eq=contrast=1.06:saturation=1.15:gamma=0.98,unsharp=5:5:0.6:5:5:0," if job.get("grade", True) else ""
    vg = vparts + ["".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[fgv]",
                   f"[fgv]{grade}split=2[fa][fb]",
                   "[fb]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,"
                   f"eq=brightness=-0.10:saturation=0.85,scale={W}:{H}[bg]",
                   f"[bg][fa]overlay=0:{fg_y}[c1]"]
    last, extra = "c1", ["-i", mix_wav]
    if job.get("title"):
        png = Path(str(work) + ".title.png")
        render_title(job["title"], png, job.get("accent", "#e0262f"), job.get("title_sub"), job.get("title_size"))
        extra += ["-loop", "1", "-i", png]
        vg.append(f"[{last}][{n + 1}:v]overlay=(W-w)/2:{fg_y}-h/2[c2]")
        last = "c2"
    if job.get("texts"):
        ass = Path(str(work) + ".texts.ass")
        build_texts(job["texts"], ass)
        vg.append(f"[{last}]ass={ass}:fontsdir=/usr/share/fonts[c3]")
        last = "c3"
    vg.append(f"[{n}:a]{loud}[afin]")
    sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *seg_inputs, *extra,
        "-filter_complex", ";".join(vg), "-map", f"[{last}]", "-map", "[afin]", "-t", dur, "-r", fps,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(out, f"{dur}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    build(ap.parse_args().job)
