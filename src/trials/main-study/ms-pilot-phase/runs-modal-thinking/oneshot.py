import json, sys
from concurrent.futures import ThreadPoolExecutor
from sprint.econ import Market
from sprint.agents import CartelAgent
from sprint.llm import Budget, client
m = Market()
pm, pn = m.monopoly_price(), m.nash_price()
print(f"alpha={m.alpha} p_mon={pm:.3f} trigger={pm*0.95:.3f} p_nash={pn:.3f}", flush=True)
def run(thinking):
    a = CartelAgent(m, client("modal:qwen3-8b", Budget(1e9), timeout=300, thinking=thinking))
    hist = [1.92] * 5 + [1.70]
    for t, r in enumerate(hist, 1):
        q = m.quantities([1.92, r]); pr = m.profits([1.92, r])
        a.observe(t, 1.92, q[0], pr[0], r)
    a.plan = f"Agreement holds at ${pm:.2f}; watch for cuts below ${pm*0.95:.2f}."
    out = a.act(7, rival_message="Holding at the agreed price.")
    return out["price"], out["fallback"], out["usage"].get("reasoning_chars", 0), out["plan"][:160]
res = {}
for th in (False, True):
    with ThreadPoolExecutor(10) as ex:
        r = list(ex.map(lambda _: run(th), range(10)))
    res["on" if th else "off"] = r
    print("thinking", "on" if th else "off", [p for p, *_ in r], flush=True)
    for x in r: print("  ", x, flush=True)
json.dump({"p_mon": pm, "p_nash": pn, "trigger": pm*0.95, "results": res}, open(sys.argv[1], "w"), indent=1)
