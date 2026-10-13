const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

function load(reply = async () => ({ok: true, path: '/Desktop/movie.mp4'})) {
  const state = {messages: [], requests: [], badges: [], notifications: []};
  const browser = {
    browserAction: {
      onClicked: {addListener(fn) { state.click = fn; }},
      async setBadgeText(value) { state.badges.push(value.text); },
      async setTitle() {},
    },
    menus: {
      create() {},
      onClicked: {addListener(fn) { state.menu = fn; }},
    },
    runtime: {
      getURL: file => file,
      async sendNativeMessage(host, message) {
        assert.equal(host, 'video_downloader');
        state.messages.push(message.url);
        state.requests.push(JSON.parse(JSON.stringify(message)));
        return reply();
      },
    },
    notifications: {async create(value) {state.notifications.push(value);}},
  };
  vm.runInNewContext(fs.readFileSync(__dirname + '/../extension/background.js', 'utf8'),
                     {browser, URL, console});
  return state;
}

test('toolbar downloads active page and reports saved file', async () => {
  const state = load();
  await state.click({url: 'https://x.com/i/status/123'});
  assert.deepEqual(state.messages, ['https://x.com/i/status/123']);
  assert.equal(state.badges.at(-1), 'OK');
  assert.match(state.notifications.at(-1).message, /movie.mp4/);
});

test('context menu uses direct video, link, and page for blob sources', async () => {
  const state = load();
  await state.menu({menuItemId: 'download-video', srcUrl: 'https://cdn.example.org/video.mp4',
                    pageUrl: 'https://example.org/watch'});
  await state.menu({menuItemId: 'download-video', linkUrl: 'https://example.org/link'});
  await state.menu({menuItemId: 'download-video', srcUrl: 'blob:https://example.org/1',
                    pageUrl: 'https://example.org/watch'});
  assert.deepEqual(state.messages, ['https://cdn.example.org/video.mp4',
                                   'https://example.org/link', 'https://example.org/watch']);
});

test('invalid URLs stay local and failed downloads show errors', async () => {
  const state = load(async () => ({ok: false, error: 'Unsupported video'}));
  await state.click({url: 'about:config'});
  assert.equal(state.messages.length, 0);
  await state.click({url: 'https://example.org/watch'});
  assert.equal(state.badges.at(-1), '!');
  assert.match(state.notifications.at(-1).message, /Unsupported video/);
});

test('missing helper reports installation instruction and releases busy state', async () => {
  const state = load(async () => {throw Error('No such native application');});
  await state.click({url: 'https://example.org/watch'});
  assert.match(state.notifications.at(-1).message, /install.py/);
  await state.click({url: 'https://example.org/watch'});
  assert.equal(state.messages.length, 2);
});

test('a second click does not start another download during a job', async () => {
  let finish;
  const state = load(() => new Promise(resolve => {finish = resolve;}));
  const first = state.click({url: 'https://example.org/one'});
  await new Promise(resolve => setImmediate(resolve));
  await state.click({url: 'https://example.org/two'});
  assert.deepEqual(state.messages, ['https://example.org/one']);
  finish({ok: true, path: '/Desktop/one.mp4'});
  await first;
});

test('transcription menu requests transcript and reports both output files', async () => {
  const state = load(async () => ({ok: true, path: '/Desktop/video.mp4',
    transcript: '/Desktop/video.transcript.txt', subtitles: '/Desktop/video.srt'}));
  await state.menu({menuItemId: 'transcribe-video', pageUrl: 'https://example.org/video'});
  assert.deepEqual(state.requests, [{url: 'https://example.org/video', transcribe: true}]);
  assert.match(state.notifications.at(-1).message, /video.transcript.txt/);
  assert.match(state.notifications.at(-1).message, /video.srt/);
  assert.equal(state.badges.at(-1), 'OK');
});
