# Datasets used for qualitative calibration

V1 does not vendor GEO matrices. Parameters are calibrated to **published qualitative directions** from these accessions. Quantitative genome-wide fits are post-v1.

| Accession | Use |
| :--- | :--- |
| GSE52814 | Pignatta 2014 reciprocal methylomes / transcriptomes |
| GSE118371 | Pignatta 2018 HDG3 |
| GSE157145 | Satyaki/Gehring Pol IV and dosage |
| GSE280598 / GSE295007 | Seed atlas / extension sets |
| GSE104240 | Williams/Gehring ROS1 transgenerational |
| GSE197717, GSE94972, GSE126932, GSE123602, GSE243032, GSE14570, GSE30511 | Mechanism/extension sets |
| GSE76076 | *A. lyrata* schema boundary (must not validate as `arabidopsis-gehring-v1`) |

Held-out checks: opposite cross direction of each trained pair, and `DMR_NULL1` plus shared DME/ROS1 targets as falsifiers.
