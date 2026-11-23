# How the Python implementation works

Use `encrypt_channel` to run Algorithm 3 with a known mask and permutations. Use `encrypt_rgb` to reproduce the complete experiment from a plaintext image. Both return a new NumPy array with the input shape and uint8 dtype.

## Algorithm 3 by hand

Consider a two-row image with plaintext rows [1, 2, 3] and [4, 5, 6]. Choose a zero mask, row destinations [1, 0], and column destinations [2, 0, 1]. Python counts from zero, so the middle column is 1. For an even width, the code starts at the right of the two middle columns.

| Logical position | Terms used | Value |
|---|---|---:|
| Top middle | 2 | 2 |
| Bottom middle | 5 + 2 above | 7 |
| Top right | 3 + 2 inward | 5 |
| Bottom right | 6 + 5 above + 7 inward + 2 diagonal | 20 |
| Top left | 1 + 2 inward | 3 |
| Bottom left | 4 + 3 above + 7 inward + 2 diagonal | 16 |

The logical rows are [3, 2, 5] and [16, 7, 20]. Logical row 0 goes to output row 1, and logical column 0 goes to output column 2. Applying both permutations gives the following executable example.

```python
import numpy as np
from algorithm3 import encrypt_channel

p = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8)
cipher = encrypt_channel(p, [1, 0], [2, 0, 1], np.zeros_like(p))
np.testing.assert_array_equal(cipher, [[7, 20, 16], [2, 5, 3]])
```

With a nonzero mask, every cell starts with its own plaintext byte plus its mask byte. All sums wrap modulo 256.

## Reading encrypt_channel

| Paper lines | Python expression | What it computes |
|---|---|---|
| 1 | `t = p.shape[1] // 2` | Converts the paper's one-based middle column to a zero-based index. |
| 2, 9–11 | `np.cumsum(base[:, t]) % 256` | Seeds the top middle and accumulates the plaintext and mask down the center. |
| 3–8, 12–21 | `inner`, `increments`, `np.cumsum(increments)` | For each outward column, adds the adjacent inward column and, below the top row, its preceding row. The vertical cumulative sum supplies the remaining dependency on the cell above. |
| All writes to C | `cipher[np.ix_(b1, b2)] = d` | Places logical cell (i, j) at ciphertext position (b1[i], b2[j]). |

This final permutation works because every ciphertext reference in the paper uses the same pair of destination maps. The code can therefore evaluate the recurrence in logical coordinates and move the bytes once at the end. It widens arithmetic to int64 before accumulation. The two permutation vectors must each contain every index on their axis exactly once.

## From a color image to three calls to Algorithm 3

| Function | Paper | Input and output |
|---|---|---|
| `image_key` | Algorithm 1 | Hashes the decoded RGB bytes with SHA-256, reads eight big-endian 32-bit words, then combines and scales their sums to produce x, y, s, w and v. The last three names correspond to σ₁, ω₁ and ω₂. |
| `keystream` | Algorithm 2 | Updates x and y together from the previous state. It discards the first 49 updated states. Sorting two segments of x yields the row and column destinations. Scaling y by 10¹⁰, taking the floor and reducing modulo 256 yields mask bytes, filled down columns. |
| `encrypt_rgb` | Section III-D, Eqs. 6–8 | Builds the planes R, R XOR G and R XOR G XOR B. The first plane uses the original parameters, the second swaps x and y, and the third swaps w and v. Each plane gets its own keystream. The function encrypts the planes sequentially and stacks the results in RGB order. |

```python
from PIL import Image
import numpy as np
from algorithm3 import encrypt_rgb

with Image.open("data/4.2.03.tiff") as image:
    rgb = np.asarray(image.convert("RGB"))
Image.fromarray(encrypt_rgb(rgb)).save("encrypted.png")
```

The full-image wrapper requires a uint8 array of shape (height, width, 3) with height and width at least two so Algorithm 2 can extract both x segments. Algorithm 3 itself also accepts single-row and single-column planes when supplied with the mask and permutations.

## How benchmark.py verifies the code

`exact_checks()` generates inputs with a fixed seed. A scalar implementation reads and writes each byte at its permuted location. The test asserts byte-for-byte equality with the cumulative-sum implementation for seven shapes. This isolates Algorithm 3 from key generation and image choice.

`run(folder)` locates one TIFF for each benchmark identifier, records its decoded RGB hash, encrypts the image, then encrypts a one-bit-modified copy with its newly derived key. It writes one CSV row per measurement. The `paper` column preserves the printed reference and `delta` is measured minus paper. Unexpected differences raise an assertion at the end. The explicitly flagged discrepancies and their treatment are described in [the results report](RESULTS.md).
