# Seed lifecycle

Primary causal window: parental reproductive state → central cell and sperm → atomic double fertilization → embryo, endosperm, seed coat at 3, 5, and 7 DAP.

```text
 sporophyte ─┬─ female gametophyte: egg (1m) + central cell (2 polar nuclei)
             └─ male gametophyte: two sister sperm (1p, identical)
                    │
                    │  DME acts in the central cell
                    │  ROS1 acts in sperm
                    ▼
            atomic double fertilization
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
     embryo      endosperm     seed coat
     1m:1p        2m:1p         2m maternal
     heritable    terminal      terminal
```

DAP 3: preglobular embryo, nuclear endosperm.
DAP 5: globular embryo, cellularization begins (advanced if HDG3 is PEG).
DAP 7: heart-stage embryo, cellularized endosperm.

Endosperm subtypes: peripheral, micropylar, chalazal cyst, chalazal nodule.

The ROS1 homeostasis protocol uses coarse vegetative generations and is firewalled from imprinting claims (`world.protocol_firewall = imprinting_claims_forbidden`).
