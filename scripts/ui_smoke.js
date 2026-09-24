// Lightweight host bridge smoke test for the bundled MCP Apps card resource.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; this.listeners = {}; }
  append(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
}
const elements = { summary: new Element('p'), cards: new Element('div'), only: new Element('input') };
const sent = [];
const listeners = {};
const parent = { postMessage(message) { sent.push(message); } };
const window = { parent, addEventListener(name, handler) { listeners[name] = handler; } };
const document = { createElement: tag => new Element(tag), getElementById: id => elements[id] };
const html = fs.readFileSync('doname/ui/cards.html', 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(script, 'inline app script exists');
vm.runInNewContext(script, { window, document }, { timeout: 1000 });
assert.strictEqual(sent[0].method, 'ui/initialize');
listeners.message({ source: parent, data: { jsonrpc: '2.0', id: 1, result: { protocolVersion: '2026-01-26' } } });
assert.strictEqual(sent[1].method, 'ui/notifications/initialized');
listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: {
  structuredContent: { summary: '1 eligible', candidates: [{ name: 'sample', match: 'pass', reasons: [], domains: [{
    domain: 'sample.com', status: 'available_at_provider', registration_price: { amount: '12.00', currency: 'EUR', period_years: 1 },
    renewal_price: null, registrability: { source: 'SyntheticProvider', checked_at: '2026-01-01T00:00:00Z' }
  }, { domain: 'sample.fr', status: 'unavailable_at_provider', registration_price: null,
    renewal_price: null, registrability: { source: 'SyntheticProvider', checked_at: '2026-01-01T00:00:00Z' }
  }] }], excluded: [] }
} } });
assert.strictEqual(elements.cards.children.length, 1);
assert.strictEqual(elements.cards.children[0].children[0].textContent, 'sample ');
assert.strictEqual(elements.cards.children[0].children[1].children[0].textContent, 'sample.com · Available at provider');
elements.only.checked = true;
elements.only.listeners.change();
assert.strictEqual(elements.cards.children[0].children.length, 2);
console.log('MCP Apps handshake and card rendering: OK');
