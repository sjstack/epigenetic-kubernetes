from __future__ import annotations


def dyads_from_fraction(n: int, frac: float) -> list[list[int]]:
    k = int(round(n * frac))
    return [[1, 1] for _ in range(k)] + [[0, 0] for _ in range(n - k)]


def sites_from_fraction(n: int, frac: float) -> list[int]:
    k = int(round(n * frac))
    return [1] * k + [0] * (n - k)


def dyad_fraction(dyads: list[list[int]]) -> float:
    if not dyads:
        return 0.0
    meth = sum(a + b for a, b in dyads)
    return meth / (2 * len(dyads))


def site_fraction(sites: list[int]) -> float:
    if not sites:
        return 0.0
    return sum(sites) / len(sites)


def replicate_dyads(dyads: list[list[int]]) -> list[list[int]]:
    """One daughter of semiconservative replication: parental Watson kept, new Crick empty."""
    return [[int(w), 0] for w, _c in dyads]


def maintain_dyads(dyads: list[list[int]], rate: float, rng) -> list[list[int]]:
    out: list[list[int]] = []
    for w, c in dyads:
        w, c = int(w), int(c)
        if w and not c:
            c = int(rng.random() < rate)
        elif c and not w:
            w = int(rng.random() < rate)
        out.append([w, c])
    return out


def replicate_chh(sites: list[int]) -> list[int]:
    return [0 for _ in sites]


def rebuild_sites(n: int, rate: float, rng) -> list[int]:
    return [int(rng.random() < rate) for _ in range(n)]


def actively_demethylate(dyads: list[list[int]], rate: float, rng) -> list[list[int]]:
    out: list[list[int]] = []
    for w, c in dyads:
        nw = 0 if (w and rng.random() < rate) else int(w)
        nc = 0 if (c and rng.random() < rate) else int(c)
        out.append([nw, nc])
    return out


def mean_context(copy: dict, locus_id: str, context: str) -> float:
    loc = copy["loci"][locus_id]
    if context == "chh":
        return site_fraction(loc["chh"])
    return dyad_fraction(loc[context])
