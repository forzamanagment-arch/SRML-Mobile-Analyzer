import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

test("single-file offline page contains valid self-contained JavaScript", async () => {
  const html = await readFile(new URL("./analyzer-offline.html", import.meta.url), "utf8");
  const scripts = [...html.matchAll(/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/g)];
  assert.equal(scripts.length, 1);
  assert.doesNotThrow(() => new vm.Script(scripts[0][1]));
  assert.doesNotMatch(html, /\\bfetch\\s*\\(|XMLHttpRequest|WebSocket|sendBeacon/);
  assert.match(html, /file\\.arrayBuffer\\(\\)/);
});
