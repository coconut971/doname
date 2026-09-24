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
    this.hidden = false;
    this.disabled = false;
    this.value = '';
    this.title = '';
    this.attributes = {};
  }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this._text = String(value ?? ''); this.children = []; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  removeEventListener(name, handler) { if (this.listeners[name] === handler) delete this.listeners[name]; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.focused = true; }
  getBoundingClientRect() { return { width: 720, height: 240 }; }
}
function findAll(root, className) {
  const result = [];
  if (String(root.className || '').split(/\s+/).includes(className)) result.push(root);
  for (const child of root.children) result.push(...findAll(child, className));
  return result;
}

async function main() {
  const elements = {
    cards: new Element('div'),
    'quick-check': new Element('form'),
    'quick-label': new Element('label'),
    'domain-query': new Element('input'),
    'quick-submit': new Element('button'),
    'quick-status': new Element('p'),
    'quick-result': new Element('div')
  };
  const sent = [];
  const listeners = {};
  const parent = { postMessage(message) { sent.push(message); } };
  let timerId = 0;
  const window = {
    parent,
    addEventListener(name, handler) { listeners[name] = handler; },
    removeEventListener(name, handler) { if (listeners[name] === handler) delete listeners[name]; },
    setTimeout() { return ++timerId; },
    clearTimeout() {}
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
  assert.match(html, /id="quick-check"/);
  assert.match(html, /method:'tools\/call'/);
  assert.match(html, /ui\/resource-teardown/);
  assert.doesNotMatch(html, /Available only|Disponibles uniquement|switch-track/i);
  const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  assert(script, 'inline app script exists');
  vm.runInNewContext(script, { window, document, ResizeObserver }, { timeout: 1000 });
  assert.strictEqual(sent[0].method, 'ui/initialize');
  assert.deepStrictEqual(Array.from(sent[0].params.appCapabilities.availableDisplayModes), ['inline', 'fullscreen']);
  listeners.message({ source: parent, data: { jsonrpc: '2.0', id: 1, result: {
    protocolVersion: '2026-01-26', hostCapabilities: { serverTools: {} }, hostContext: {
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
  assert.strictEqual(elements['quick-check'].hidden, false, 'exact-domain action appears when the host proxies server tools');

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
      ] }], excluded: [{ name: 'hidden-candidate', match: 'fail', reasons: ['not available'], domains: [] }]
    }
  } } });
  assert.strictEqual(findAll(elements.cards, 'candidate').length, 1);
  assert.strictEqual(findAll(elements.cards, 'candidate-title')[0].children[0].textContent, 'sample');
  assert(elements.cards.textContent.includes('1/2 dispo'));
  assert(elements.cards.textContent.includes(new Intl.NumberFormat('fr-FR', {
    style: 'currency', currency: 'USD', currencyDisplay: 'code'
  }).format(12)));
  assert(elements.cards.textContent.includes('GoDaddy'));
  assert(elements.cards.textContent.includes('Renouvellement'));
  assert(!elements.cards.textContent.includes(checkedAt), 'raw timestamp stays out of the compact card');
  assert(!elements.cards.textContent.includes('hidden-candidate'), 'excluded candidates stay with the AI explanation');
  assert.strictEqual(findAll(elements.cards, 'checked').length, 0, 'freshness details stay out of the compact card');
  assert(findAll(elements.cards, 'more')[0].textContent.includes('Sources & renouvellement'));
  assert.strictEqual(findAll(elements.cards, 'domain-card').length, 2);
  assert.deepStrictEqual(findAll(elements.cards, 'domain-card').map(card => card.title), ['sample.com', 'sample.fr']);

  let prevented = false;
  elements['domain-query'].value = 'probe.example.fr';
  const searchPromise = elements['quick-check'].listeners.submit({ preventDefault() { prevented = true; } });
  assert.strictEqual(prevented, true);
  assert.strictEqual(elements['quick-status'].textContent, 'Recherche en cours…');
  const toolCall = sent.at(-1);
  assert.strictEqual(toolCall.method, 'tools/call');
  assert.strictEqual(toolCall.params.name, 'check_domains');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(toolCall.params.arguments)), { domains: ['probe.example.fr'] });
  listeners.message({ source: parent, data: { jsonrpc: '2.0', id: toolCall.id, result: { structuredContent: {
    summary: '1 available_at_provider', checked: 1, domains: [{
      domain: 'probe.example.fr', status: 'available_at_provider', reason: 'provider_available',
      registration: null, dns: null,
      registrability: { status: 'available', source: 'GoDaddy', checked_at: checkedAt, age_seconds: 1 },
      registration_price: { amount: '15.00', currency: 'EUR', period_years: 1, kind: 'registration', provider: 'GoDaddy', checked_at: checkedAt, indicative: true },
      renewal_price: null
    }]
  } } } });
  await searchPromise;
  assert.strictEqual(findAll(elements['quick-result'], 'domain-card').length, 1);
  assert(elements['quick-result'].textContent.includes('Disponible'));
  assert(elements['quick-result'].textContent.includes('GoDaddy'));
  assert.strictEqual(elements['quick-status'].hidden, true);
  assert.strictEqual(elements['quick-submit'].disabled, false);

  elements['domain-query'].value = 'Lune';
  const nameSearchPromise = elements['quick-check'].listeners.submit({ preventDefault() {} });
  const nameSearch = sent.at(-1);
  assert.strictEqual(nameSearch.method, 'tools/call');
  assert.strictEqual(nameSearch.params.name, 'screen_names');
  assert.deepStrictEqual(JSON.parse(JSON.stringify(nameSearch.params.arguments)), {
    names: ['Lune'], extensions: ['com', 'fr', 'ai', 'io', 'app'], match: 'any', available_only: true
  });
  listeners.message({ source: parent, data: { jsonrpc: '2.0', id: nameSearch.id, result: { structuredContent: {
    summary: '1 eligible, 0 excluded, 0 unverified candidate names.',
    excluded_summary: { excluded: 0, unverified: 0 },
    candidates: [{ name: 'lune', match: 'pass', reasons: [], domains: [{
      domain: 'lune.ai', status: 'available_at_provider', reason: 'provider_available',
      registration: null, dns: null,
      registrability: { status: 'available', source: 'GoDaddy', checked_at: checkedAt, age_seconds: 1 },
      registration_price: { amount: '79.00', currency: 'EUR', period_years: 1, kind: 'registration', provider: 'GoDaddy', checked_at: checkedAt, indicative: true },
      renewal_price: null
    }] }], excluded: []
  } } } });
  await nameSearchPromise;
  assert.strictEqual(findAll(elements['quick-result'], 'candidate').length, 1);
  assert(elements['quick-result'].textContent.includes('.ai'));
  assert(!elements['quick-result'].textContent.includes('.com'), 'unavailable extensions stay out of available-only name results');
  assert(elements['quick-result'].textContent.includes('GoDaddy'));

  elements['domain-query'].value = 'absent';
  const emptySearchPromise = elements['quick-check'].listeners.submit({ preventDefault() {} });
  const emptySearch = sent.at(-1);
  listeners.message({ source: parent, data: { jsonrpc: '2.0', id: emptySearch.id, result: { structuredContent: {
    summary: '0 eligible, 0 excluded, 1 unverified candidate names.',
    excluded_summary: { excluded: 0, unverified: 1 }, candidates: [], excluded: []
  } } } });
  await emptySearchPromise;
  assert(elements['quick-result'].textContent.toLowerCase().includes('aucun domaine confirmé disponible'));
  assert(elements['quick-result'].textContent.includes('certaines extensions n’ont pas pu être vérifiées'));
  assert(!elements['quick-result'].textContent.includes('Aucune réponse exploitable'));

  listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/host-context-changed', params: {
    locale: 'en-US', theme: 'dark', platform: 'web'
  } } });
  assert.strictEqual(document.documentElement.lang, 'en-US');
  assert.strictEqual(document.documentElement.dataset.theme, 'dark');
  assert.strictEqual(document.documentElement.dataset.platform, 'web');
  assert(elements.cards.textContent.includes(new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', currencyDisplay: 'code'
  }).format(12)));

  listeners.message({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: {
    structuredContent: { summary: '1 unverified', excluded_summary: { excluded: 0, unverified: 1 }, candidates: [], excluded: [{
      name: 'sample', match: 'unknown', reasons: [], domains: [{ domain: 'sample.fr', status: 'not_found_in_registration_data',
        registration_price: null, renewal_price: null,
        registration: { source: 'rdap.example.net', status: 'not_found', checked_at: checkedAt },
        registrability: { source: 'GoDaddy', status: 'unconfirmed', checked_at: checkedAt }
      }]
    }] }
  } } });
  assert(elements.cards.textContent.includes('No names match these criteria.'));
  assert(!elements.cards.textContent.includes('sample'));

  const oldHandler = listeners.message;
  oldHandler({ source: parent, data: { jsonrpc: '2.0', id: 'close-42', method: 'ui/resource-teardown', params: { reason: 'host closed view' } } });
  assert.strictEqual(sent.at(-1).jsonrpc, '2.0');
  assert.strictEqual(sent.at(-1).id, 'close-42');
  assert.deepStrictEqual(Object.keys(sent.at(-1).result), []);
  assert.strictEqual(elements.cards.children.length, 0);
  assert.strictEqual(elements['quick-result'].children.length, 0);
  assert.strictEqual(elements['quick-check'].listeners.submit, undefined);
  assert.strictEqual(listeners.message, undefined);
  assert.strictEqual(observer.disconnected, true);
  const afterTeardown = sent.length;
  oldHandler({ source: parent, data: { jsonrpc: '2.0', method: 'ui/notifications/tool-result', params: { structuredContent: {} } } });
  observer.callback();
  assert.strictEqual(sent.length, afterTeardown);
  console.log('MCP Apps handshake, compact cards, exact-domain and name/TLD search, locale/theme updates and teardown: OK');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
