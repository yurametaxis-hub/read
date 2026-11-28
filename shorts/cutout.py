#!/usr/bin/env python3
"""Cut a player out of a club portrait (plain coloured backdrop) with MODNet portrait matting.

    python3 shorts/cutout.py MODEL.onnx IN.png OUT.png [--box auto|x,y,w,h]

--box auto finds the photo inside a website screenshot by its orange backdrop (the Hull City player pages);
give x,y,w,h for anything else. Output is an RGBA png of the cropped photo with a soft alpha matte.
MODNet: Apache-2.0, onnx export from huggingface.co/Xenova/modnet.
"""
import sys

import numpy as np
import onnxruntime as ort
from PIL import Image


def find_photo(img):
    a = np.asarray(img.convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    orange = (r > 200) & (g > 110) & (g < 200) & (b < 100)
    orange[:, : a.shape[1] // 2] = False          # the photo sits in the right half of the page
    cols = np.where(orange.sum(0) > 40)[0]
    rows = np.where(orange.sum(1) > 40)[0]
    x0, x1, y0, y1 = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    return x0, y0, x1 - x0, y1 - y0


def matte(sess, rgb, ref=512):
    h, w = rgb.shape[:2]
    if h >= w:
        rh, rw = ref, int(w / h * ref)
    else:
        rw, rh = ref, int(h / w * ref)
    rh, rw = max(32, rh - rh % 32), max(32, rw - rw % 32)
    x = np.asarray(Image.fromarray(rgb).resize((rw, rh), Image.BILINEAR)).astype(np.float32) / 255.0
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    m = sess.run(None, {"input": x})[0][0, 0]
    return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC))


def main():
    model, src, out = sys.argv[1:4]
    box = sys.argv[sys.argv.index("--box") + 1] if "--box" in sys.argv else "auto"
    img = Image.open(src).convert("RGB")
    x, y, w, h = find_photo(img) if box == "auto" else map(int, box.split(","))
    crop = np.asarray(img.crop((x, y, x + w, y + h)))
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    a = matte(sess, crop)
    Image.fromarray(np.dstack([crop, a])).save(out)
    print(out, (x, y, w, h))


if __name__ == "__main__":
    main()
