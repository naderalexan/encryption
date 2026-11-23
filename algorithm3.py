"""Gao et al. (2025), DOI 10.1109/JIOT.2025.3540097. Requires NumPy."""
import hashlib
import math
import struct
import numpy as np


def encrypt_channel(p, b1, b2, b3):
    """Algorithm 3. p and b3 are uint8 planes. Permutations are zero-based."""
    p, b1, b2, b3 = map(np.asarray, (p, b1, b2, b3))
    if p.ndim != 2 or not p.size or p.shape != b3.shape:
        raise ValueError("p and b3 must be equal-sized, nonempty planes")
    if p.dtype != np.uint8 or b3.dtype != np.uint8:
        raise TypeError("p and b3 must have dtype uint8")
    for perm, size in zip((b1, b2), p.shape):
        if (perm.dtype.kind not in "iu" or perm.shape != (size,)
                or not np.array_equal(np.sort(perm), np.arange(size))):
            raise ValueError("expected one permutation per axis")

    # Work in logical coordinates. Scatter only after computing the recurrence.
    t = p.shape[1] // 2
    base = p.astype(np.int64) + b3
    d = np.empty_like(p)
    d[:, t] = np.cumsum(base[:, t]) % 256
    for j in (*range(t + 1, p.shape[1]), *range(t - 1, -1, -1)):
        inner = d[:, j - 1 if j > t else j + 1].astype(np.int64)
        # Vertical prefix sum supplies the previous row in the current column.
        increments = base[:, j] + inner
        increments[1:] += inner[:-1]
        d[:, j] = np.cumsum(increments) % 256
    cipher = np.empty_like(p)
    cipher[np.ix_(b1, b2)] = d
    return cipher


def image_key(rgb):
    """Algorithm 1, hashing decoded RGB bytes in row-major interleaved order."""
    words = struct.unpack(">8I", hashlib.sha256(rgb.tobytes(order="C")).digest())
    def triple(i):
        return sum(words[i:i+3]) / 2**34
    x = triple(0)
    y = (x + triple(1)) / 2
    s = (y + triple(3)) / 2
    w = (s + triple(4)) / 2
    v = (w + triple(5)) / 2
    return x, y, 92*s + 8, 97*w + 3, 97*v + 3


def keystream(x, y, s, w, v, rows, cols):
    """Algorithm 2. Retain the 50th updated state first, MATLAB reshape order."""
    count = rows * cols
    if rows + cols > count:
        raise ValueError("Algorithm 2 needs rows + cols <= rows * cols")
    xs = np.empty(rows + cols)
    ys = np.empty(count)
    for i in range(-49, count):
        x, y = (math.sin(s / (1 + x*x) + y + w*x*(1-y)),
                math.sin(y - 0.8*x - 5 + v*y*(1-x)))
        if i >= 0:
            ys[i] = y
            if i < len(xs):
                xs[i] = x
    mask = (np.floor(ys * 1e10) % 256).astype(np.uint8)
    return (np.argsort(xs[:rows], kind="stable"), np.argsort(xs[rows:], kind="stable"),
            mask.reshape((rows, cols), order="F"))


def encrypt_rgb(rgb):
    """Section III-D. The independent channel computations run serially here."""
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("expected an H x W x 3 uint8 RGB image")
    x, y, s, w, v = image_key(rgb)
    fused = np.bitwise_xor.accumulate(rgb, axis=2)
    keys = [(x,y,s,w,v), (y,x,s,w,v), (x,y,s,v,w)]
    return np.stack([encrypt_channel(fused[..., k], *keystream(*key, *rgb.shape[:2]))
                     for k, key in enumerate(keys)], axis=2)
