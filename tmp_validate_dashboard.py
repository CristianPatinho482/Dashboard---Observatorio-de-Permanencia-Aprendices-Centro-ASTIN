import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/index.html"
OUT = Path("tmp_validation")
OUT.mkdir(exist_ok=True)

tabs = ["resumen", "demografia", "programas", "fichas", "temporal", "riesgos", "predictivo"]
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1500, "height": 1000}, device_scale_factor=1)
    page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"PAGEERROR: {exc}"))
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(800)
    results = {}
    for t in tabs:
        page.click(f'.tab[data-tab="{t}"]')
        page.wait_for_timeout(700)
        info = page.evaluate("""(t) => {
            const panel = document.getElementById('tab-'+t);
            const visible = getComputedStyle(panel).display !== 'none';
            const cards = [...panel.querySelectorAll('.kpi .value, .critical .rate')].slice(0, 8).map(e => e.textContent.trim());
            const tables = [...panel.querySelectorAll('table')].map(tb => ({
                id: tb.id,
                rows: tb.querySelectorAll('tbody tr').length,
                headers: tb.querySelectorAll('thead th').length
            }));
            const canvases = [...panel.querySelectorAll('canvas')].map(c => ({id: c.id, w: c.width, h: c.height}));
            const nan = panel.innerText.includes('NaN') || panel.innerText.includes('undefined') || panel.innerText.includes('Infinity');
            return {visible, cards, tables, canvases, nan, textLen: panel.innerText.length};
        }""", t)
        results[t] = info
        page.screenshot(path=str(OUT / f"{t}.png"), full_page=True)
    # filter interaction test
    page.click('.tab[data-tab="fichas"]')
    page.wait_for_timeout(300)
    before = page.locator("#tb-fichas tbody tr").count()
    page.select_option("#f-jorn", "NOCTURNA")
    page.wait_for_timeout(600)
    after = page.locator("#tb-fichas tbody tr").count()
    kpi_noct = page.locator("#kpis .kpi").first.inner_text()
    results["filtro_nocturna"] = {"filas_antes": before, "filas_despues": after, "kpi": kpi_noct}
    page.screenshot(path=str(OUT / "filtro_nocturna.png"), full_page=True)
    # console error count
    browser.close()

print(json.dumps(results, ensure_ascii=False, indent=2))
print("\nERRORES:", len(errors))
for e in errors[:20]:
    print(e)
Path("tmp_validation/resultado.json").write_text(json.dumps({"results": results, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
