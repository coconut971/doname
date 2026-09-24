// Credential-free host bridge smoke test for the bundled MCP Apps card resource.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this._text = '';
    this.listeners = {};
    this.dataset = {};
    this.style = { values: {}, setProperty(key, value) { this.values[key] = value; } };
    this.checked = false;
  }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this._text = String(value ?? ''); this.children = []; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  removeEventListener(name, handler) { if (this.listeners[name] === handler) delete this.listeners[name]; }
  getBoundingClientRect() { return { width: 720, height: 240 }; }
}
function findAll(root, className) {
  const result = [];
  if (root.className === className) result.push(root);
  for (const child of root.children) result.push(...findAll(child, className));
  return result;
}
const elements = {
  summary: new Element('p'), cards: new Element('div'), only: new Element('input'),
  'filter-label': new Element('span')
};
const sent = [];
const listeners = {};
const parent = { postMessage(message) { sent.push(message); } };
const window = {
  parent,
  addEventListener(name, handler) { listeners[name] = handler; },
  removeEventListener(name, handler) { if (listeners[name] === handler) delete listeners[name]; }
};
const document = {
  body: new Element('body'),
  documentElement: new Element('html'),
  createElement: tag => new Element(tag),
  getElementById: id => elements[id]
};
document.documentElement.lang = 'en-US';
let observer;
class ResizeObserver {
  constructor(callback) { this.callback = callback; this.disconnected = false; observer = this; }
  observe(element) { assert.strictEqual(element, document.body); }
  disconnect() { this.disconnected = true; }
}

const html = fs.readFileSync('doname/ui/cards.html', 'utf8');
assert.match(html, /availableDisplayModes:\['inline','fullscreen'\]/);
assert.match(html, /ui\/notifications\/host-context-changed/);
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(script, 'inline app script exists');
vm.runInNewContext(script, { window, document, ResizeObserver }, { timeout: 1000 });
assert.strictEqual(sent[0].method, 'ui/initialize');
assert.deepStrictEqual(Array.from(sent[0].params.appCapabilities.availableDisplayModes), ['inline', 'fullscreen']);
listeners.message({ source: parent, data: { jsonrpc: '2.0', id: 1, result: {
  protocolVersion: '2026-01-26', hostContext: {
    locale: 'fr-FR', theme: 'light', platform: 'mobile', timeZone: 'Europe/Paris',
    availableDisplayModes: ['inline', 'fullscreen'], styles: { variables: { '--color-text-primary': '#111' } }
  }
} } });
assert.strictEqual(sent[1].method, 'ui/notifications/initialized');
assert(sent.some(message => message.method === 'ui/notifications/size-changed'));
assert.strictEqual(document.documentElement.lang, 'fr-FR');
assert.strictEqual(document.documentElement.dataset.theme, 'light');
assert.strictEqual(document.documentElement.dataset.platform, 'mobile');
assert.strictEqual(document.documentElement.style.values['--color-text-primary'], '#111');
assert.strictEqual(elements['filter-label'].textContent, 'Disponibles uniquement');

const checkedAt = '2026-09-24T18:03:58Z';
listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: {
  structuredContent: {
    summary: '1 eligible, 0 excluded, 0 unverified candidate names.',
    excluded_summary: { excluded: 0, unverified: 0 },
    candidates: [{ name: 'sample', match: 'pass', reasons: [], domains: [
      { domain: 'sample.com', status: 'available_at_provider',
        registration_price: { amount: '12.00', currency: 'USD', period_years: 1, provider: 'GoDaddy' },
        renewal_price: { amount: '19.00', currency: 'USD', period_years: 1, provider: 'GoDaddy' },
        registrability: { source: 'GoDaddy', status: 'available', checked_at: checkedAt } },
      { domain: 'sample.fr', status: 'unavailable_at_provider', registration_price: null,
        renewal_price: null, registrability: { source: 'GoDaddy', status: 'unavailable', checked_at: checkedAt } }
    ] }], excluded: []
  }
} } });
assert.strictEqual(findAll(elements.cards, 'candidate').length, 1);
assert.strictEqual(findAll(elements.cards, 'candidate-title')[0].children[0].textContent, 'sample');
assert(elements.cards.textContent.includes('1 / 2 extensions disponibles chez le fournisseur'));
assert(elements.cards.textContent.includes(new Intl.NumberFormat('fr-FR', {
  style: 'currency', currency: 'USD', currencyDisplay: 'code'
}).format(12)));
assert(elements.cards.textContent.includes('GoDaddy'));
assert(elements.cards.textContent.includes('Renouvellement'));
assert(!elements.cards.textContent.includes(checkedAt), 'raw timestamp stays out of the compact card');
const checked = findAll(elements.cards, 'checked')[0];
assert.strictEqual(checked.title.length > 0, true, 'exact localized check time remains available as a title');
assert.strictEqual(findAll(elements.cards, 'domain-card').length, 2);

elements.only.checked = true;
elements.only.listeners.change();
assert.strictEqual(findAll(elements.cards, 'domain-card').length, 1);
assert(elements.cards.textContent.includes('sample.com'));
assert(!elements.cards.textContent.includes('sample.fr'));

listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/host-context-changed', params: {
  locale: 'en-US', theme: 'dark', platform: 'web'
} } });
assert.strictEqual(document.documentElement.lang, 'en-US');
assert.strictEqual(document.documentElement.dataset.theme, 'dark');
assert.strictEqual(document.documentElement.dataset.platform, 'web');
assert(elements.cards.textContent.includes(new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', currencyDisplay: 'code'
}).format(12)));

elements.only.checked = false;
elements.only.listeners.change();
listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: {
  structuredContent: { summary: '1 unverified', excluded_summary: { excluded: 0, unverified: 1 }, candidates: [], excluded: [{
    name: 'sample', match: 'unknown', reasons: [], domains: [{ domain: 'sample.fr', status: 'not_found_in_registration_data',
      registration_price: null, renewal_price: null,
      registration: { source: 'rdap.example.net', status: 'not_found', checked_at: checkedAt },
      registrability: { source: 'GoDaddy', status: 'unconfirmed', checked_at: checkedAt }
    }]
  }] }
} } });
assert(elements.cards.textContent.includes('rdap.example.net'));
assert(elements.cards.textContent.includes('GoDaddy · unconfirmed'));
assert(elements.cards.textContent.includes('Not found in RDAP'));

const oldHandler = listeners.message;
oldHandler({ source: parent, data: { jsonrpc: '2.0', id: 'close-42', method: 'ui/resource-teardown', params: { reason: 'host closed view' } } });
assert.strictEqual(sent.at(-1).jsonrpc, '2.0');
assert.strictEqual(sent.at(-1).id, 'close-42');
assert.deepStrictEqual(Object.keys(sent.at(-1).result), []);
assert.strictEqual(elements.cards.children.length, 0);
assert.strictEqual(elements.only.listeners.change, undefined);
assert.strictEqual(listeners.message, undefined);
assert.strictEqual(observer.disconnected, true);
const afterTeardown = sent.length;
oldHandler({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: { structuredContent: {} } } });
observer.callback();
assert.strictEqual(sent.length, afterTeardown);
console.log('MCP Apps handshake, responsive cards, locale/theme updates and teardown: OK');
