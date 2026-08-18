from __future__ import annotations

from epik.api.outbound import OutboundAPI, attach_consumer, seed_dashboard
from epik.simulate import run_cross


def test_digest_independent_of_consumers():
    e0, w0 = run_cross("Col-0", "Ler", seed=8, to_dap=3)
    e1, _ = run_cross("Col-0", "Ler", seed=8, to_dap=3)
    sink: list = []
    attach_consumer(e1, sink)
    # attaching after the run still must not mutate prior digest
    assert e0.digest() == e1.digest()
    e2, _ = run_cross("Col-0", "Ler", seed=8, to_dap=3)
    attach_consumer(e2, [])
    attach_consumer(e2, [])
    attach_consumer(e2, [])
    assert e2.digest() == e0.digest()
    dash = seed_dashboard(w0)
    assert dash["read_only"] is True
    api = OutboundAPI(e0)
    assert api.digest() == e0.digest()
    assert api.query(kind="set_world")
    exported = api.export()
    assert exported["digest"] == e0.digest()
