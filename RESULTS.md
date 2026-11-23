# Comparison with the paper

The run used all nine 512 × 512 USC-SIPI RGB images named in Tables II–VI of Gao et al. (2025), DOI 10.1109/JIOT.2025.3540097. Of 288 printed comparisons, 233 passed their tolerances, 54 plaintext correlations differed under the printed image labels, and one published MSE exceeded the mathematical maximum. Of the 180 ciphertext-related entries, all 179 valid entries passed.

## Aggregate results

Means below use the individual published entries and the corresponding Python measurements. The MSE row uses the same 26 valid image/channel pairs on both sides. The correlation row averages magnitudes to avoid cancellation, and checks each original signed coefficient against its printed counterpart.

| Paper table and metric | Pairs | Paper mean | Python mean | Largest absolute difference | Acceptance margin |
|---|---:|---:|---:|---:|---|
| III · Absolute ciphertext correlation | 81 | 0.001316 | 0.001204 | 0.005574 | 0.011 |
| IV · Plaintext entropy (bits) | 27 | 6.946948 | 6.947003 | 0.000090 | 0.0001 |
| IV · Ciphertext entropy (bits) | 27 | 7.999289 | 7.999307 | 0.000208 | 0.00035 |
| V · NPCR (%) | 9 | 99.608489 | 99.608598 | 0.021739 | 0.03 percentage points |
| V · UACI (%) | 9 | 33.459378 | 33.459441 | 0.057684 | 0.12 percentage points |
| VI · MSE | 26 | 8800.730769 | 8806.197400 | 40.784283 | 2% of each reference |
| VI · PSNR (dB) | 27 | 8.793037 | 8.790409 | 0.020611 | 0.09 dB |

## Sensitivity to a one-bit change, by image

The test flips the least significant bit of the upper-left red pixel, derives a fresh key, and encrypts again. NPCR is the percentage of RGB channel samples that change. UACI is their mean absolute change as a percentage of 255, including samples with zero change. Each figure in the table is a percentage.

| USC-SIPI image | NPCR paper | NPCR Python | UACI paper | UACI Python |
|---|---:|---:|---:|---:|
| 2.1.01 | 99.6085 | 99.6063 | 33.4725 | 33.4978 |
| 2.1.02 | 99.6083 | 99.5909 | 33.4627 | 33.4499 |
| 2.1.03 | 99.6067 | 99.6070 | 33.4601 | 33.4649 |
| 2.1.04 | 99.6086 | 99.6054 | 33.4548 | 33.5125 |
| 2.1.05 | 99.6076 | 99.6293 | 33.4577 | 33.4721 |
| 2.1.06 | 99.6087 | 99.6053 | 33.4532 | 33.4630 |
| 4.2.01 | 99.6098 | 99.6168 | 33.4577 | 33.4225 |
| 4.2.03 | 99.6095 | 99.6006 | 33.4564 | 33.4251 |
| 4.2.06 | 99.6087 | 99.6157 | 33.4593 | 33.4272 |

## Why some rows disagree

**Table II, plaintext correlation.** The benchmark computes Pearson correlation over every horizontal, vertical and down-right neighboring pair within each channel. All 27 coefficients for the three miscellaneous images match within 0.00001. All 54 coefficients for the six aerial images differ from their labeled rows by more than that tolerance. Three correspondences can be verified independently.

| Actual input | Matching printed row | Coefficients within 0.00001 |
|---|---|---:|
| 2.1.01 | 2.1.04 | 9 of 9 |
| 2.1.02 | 2.1.05 | 9 of 9 |
| 2.1.03 | 2.1.06 | 9 of 9 |

For example, the horizontal red coefficient for 2.1.01 is 0.88162943. Table II prints 0.98669 under that image and 0.88162 under 2.1.04. The cause of the remaining three aerial row discrepancies is unresolved. Entropy provides a separate input check. All 27 plaintext channel entropies agree with their own Table IV labels within 0.0001 bits.

**Table VI, green channel of 4.2.03.** MSE averages the squared differences between corresponding plaintext and ciphertext samples. An 8-bit channel has a maximum possible MSE of 255² = 65,025. The printed 77,402 exceeds this bound. Inverting the paper’s PSNR formula gives 65,025 / 10^(9.2432/10) = 7,740.35. Python measured 7,725.02 and 9.25180 dB. The CSV retains 77,402 with the status “invalid published value.”

## What the comparisons establish

Shannon entropy measures the spread of byte frequencies, and adjacent-pixel correlation measures local linear dependence. MSE and PSNR measure how far ciphertext samples are from the corresponding plaintext samples. NPCR and UACI measure the response of the full pipeline to the chosen perturbation, including the change of key. The margins in the summary are benchmark tolerances chosen for this reproduction.

The paper supplies summary statistics and leaves some execution choices open, including serialization of the input to SHA-256 and the perturbation used for the differential test. This run uses interleaved RGB bytes in row-major order and one deterministic perturbation per image. The seven scalar-reference tests establish exact agreement for Algorithm 3 on those inputs. Confirming byte-for-byte agreement with the authors' complete pipeline would require a published test vector. Table VII's hardware timing was outside the reproduction.

The first comparison identified the printed-precision and labeling issues. A second run checked plaintext at the displayed precision and asserted the three shifted matches directly. The encryption code and ciphertext tolerances were the same on both runs.

For every image, channel, direction, signed difference, and row status, see [results.csv](results.csv). The [README](README.md) gives the rerun command and dataset locations.
