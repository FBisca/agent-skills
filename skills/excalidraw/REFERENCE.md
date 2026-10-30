# Excalidraw reference

Consulted from the `excalidraw` skill: the render loop, and the file-format facts `excali.py` already encodes (read them before changing it).

## Render loop

The Playwright MCP's `browser_run_code_unsafe` can't read local files (`require` is undefined) and only writes screenshots under the session's working directory. So a local server hands the JSON to excalidraw.com, which keeps everything in the browser's localStorage. Nothing is uploaded or shared.

1. Split and serve:
   - `python3 -I <sk>/scripts/split.py <slug>.excalidraw <scratch>/serve`, which writes `f<n>.json` per frame plus `all.json`
   - `python3 -I <sk>/scripts/serve.py <scratch>/serve`, in the background
2. Open `https://excalidraw.com` once with `browser_navigate`, so the page can fetch from `127.0.0.1:8765`.
3. Render each frame with `browser_run_code_unsafe`:

```js
async (page) => {
  const ctx = page.context();
  for (const f of ['f1', 'f2', 'all']) {            // the frames to look at
    const data = await page.evaluate(async (f) =>
      await (await fetch(`http://127.0.0.1:8765/${f}.json?` + Date.now())).text(), f);
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1800, height: 1100 });
    await p.addInitScript((d) => {                    // before the app loads, or it overwrites localStorage
      if (location.hostname === 'excalidraw.com') {
        localStorage.setItem('excalidraw', JSON.stringify(JSON.parse(d).elements));
        localStorage.setItem('excalidraw-state', JSON.stringify({ viewBackgroundColor: '#ffffff' }));
      }
    }, data);
    await p.goto('https://excalidraw.com/?' + f + Date.now(), { waitUntil: 'networkidle' });
    await p.waitForTimeout(2000);
    await p.mouse.click(900, 600);                    // focus the canvas; bottom-right is the help button
    await p.keyboard.press('Escape');
    await p.keyboard.press('Shift+1');                // zoom to fit
    await p.waitForTimeout(1000);
    await p.screenshot({ path: `.playwright-mcp/${f}.png` });
    await p.close();
  }
  return 'ok';
}
```

4. Read each `.playwright-mcp/<f>.png` with the Read tool. Wheel-zooming inside the page scrolls instead of zooming; to see a detail, render a smaller frame.
5. When done, stop the server and delete `.playwright-mcp/` from the working directory: its PNGs and console logs.

## File format facts

- **Elbow arrows** need `elbowed: true`, orthogonal `points` relative to the arrow's `x`/`y`, `roundness: null`, and bindings of the form `{"elementId", "mode": "orbit", "fixedPoint": [fx, fy]}`, with fx/fy just outside 0..1 on the bound side. Both bound shapes list the arrow in `boundElements`.
- **Text inside a shape or on an arrow** is a text element with `containerId` set to the owner, plus `{"id", "type": "text"}` in the owner's `boundElements`. Without both, the label floats.
- **Fonts and sizing:** Excalifont is `fontFamily: 5`. Its character width is about 0.64 × the font size; narrower estimates clip text on render. Line height is 1.25.
- **Freedraw** needs `points` relative to its `x`/`y` (the first point), `pressures: []`, `simulatePressure: true`, and `strokeOptions`.
- **No `frame` elements.** They clip anything that sticks out of them. Grouping is carried by `customData.frame` instead, which Excalidraw keeps.
- **Hand-made drawings** (measured on the user's): Excalifont, `roughness: 1`, `strokeWidth: 2`, rounded corners on most boxes, elbow arrows almost everywhere, and box fills mostly white or transparent.
