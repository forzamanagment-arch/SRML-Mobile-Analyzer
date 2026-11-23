import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

test("single-file offline page contains valid self-contained JavaScript", async () => {
  const html = await readFile(new URL("./analyzer-offline.html", import.meta.url), "utf8");
  const open = html.indexOf("<script>");
  const close = html.indexOf("</script>", open);
  assert.notEqual(open, -1);
  assert.notEqual(close, -1);
  assert.equal(html.indexOf("<script>", open + 1), -1);
  assert.doesNotThrow(() => new vm.Script(html.slice(open + 8, close)));
  for (const forbidden of ["fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon"]) {
    assert.equal(html.includes(forbidden), false);
  }
  assert.equal(html.includes("file.arrayBuffer()"), true);
});
