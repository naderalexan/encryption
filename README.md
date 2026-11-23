# Reproducing Algorithm 3 of Gao et al. (2025)

See [How the code works](CODE.md) for a worked example and [Comparison with the paper](RESULTS.md) for the numerical results and discrepancies.

The public function encrypt_channel(p, b1, b2, b3) takes one 8-bit plane, two zero-based permutations, and an 8-bit mask. Algorithm 3 seeds the first pixel in the middle column, propagates down that column, and processes each half outward. Each interior pixel includes the preceding row, the inward neighbor, and their shared diagonal. The implementation computes equivalent column prefix sums and scatters into the permuted positions. encrypt_rgb includes Algorithms 1 and 2 and Eqs. 6–8.

## Run the benchmark

From the extracted directory, with Python 3, curl, and unzip installed, run

```sh
python -m pip install numpy pillow
mkdir -p data
curl -fL https://sipi.usc.edu/database/aerials.zip -o aerials.zip
curl -fL https://sipi.usc.edu/database/misc.zip -o misc.zip
unzip -jo aerials.zip '*/2.1.0[1-6].tiff' -d data
unzip -jo misc.zip '*/4.2.0[136].tiff' -d data
python benchmark.py data > my-results.csv
```

results.csv contains the measured values and the original per-image references from Tables II–VI. input-hashes.txt identifies the decoded inputs used in this run. Correlations use all nonwrapping adjacent pairs, including the down-right diagonal. MSE and PSNR compare each original channel with its corresponding encrypted channel. The sensitivity test flips the low bit of the upper-left red sample, recomputes the plaintext-derived key, and pools the three output channels. The paper does not specify this perturbation or its trial count. Other implementation conventions include float64 states with scalar math.sin, interleaved RGB hash input, the 50th updated state as the first retained state, and column-major mask reshaping. Matching ciphertext bytes would require an authoritative test vector. Runtime on the authors' hardware was outside this comparison.

## Interpreting the checks

The exact test compares the optimized Algorithm 3 with a literal scalar recurrence on seven shapes, covering even and odd widths, single rows and columns, arbitrary permutations and modular overflow. For the tables, acceptance margins are engineering tolerances, not hypothesis tests. Absolute tolerances are 0.00035 bits for ciphertext entropy, 0.011 for ciphertext correlation, 0.09 dB for PSNR, and 0.03 and 0.12 percentage points for NPCR and UACI. MSE uses 2% relative tolerance. A nonzero exit reports any unexpected discrepancy. Close aggregate statistics alone cannot identify the authors' exact ciphertext.

The first run exposed four- and five-decimal truncation in plaintext results and mismatched aerial image labels in Table II. The second run applied displayed-precision tolerances to plaintext and explicitly tested the shifted matches. No key choices or encryption steps were adjusted to improve agreement. All 27 plaintext entropies agree within 0.0001 bits. All 27 plaintext correlations for the miscellaneous images agree within 0.00001. The 54 aerial correlations differ under the printed labels. For the first three aerial images, the next three printed rows match all 27 coefficients within 0.00001. The six original labeled rows remain in the CSV.

Table VI prints an impossible MSE of 77,402 for 4.2.03 green. Its printed PSNR of 9.2432 dB implies an MSE of about 7,740.35. The measured value is 7,725.02. The benchmark retains the printed value and flags it. All 179 other ciphertext-related entries pass their tolerances. The tests address reproduction of the reported measurements, not cryptographic strength.
