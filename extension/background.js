let downloading = false;

async function notify(title, message) {
  try {
    await browser.notifications.create({
      type: 'basic', iconUrl: browser.runtime.getURL('icon.svg'),
      title, message: String(message).slice(0, 500),
    });
  } catch (error) {
    console.error('Could not show download notification:', error);
  }
}

async function download(url, transcribe = false) {
  if (downloading) {
    await notify('Download in progress', 'Wait for the current video to finish downloading.');
    return;
  }
  try {
    const parsed = new URL(url);
    if (!['https:', 'http:'].includes(parsed.protocol)) throw Error('Unsupported URL');
  } catch {
    await notify('Choose a video', 'Open a video page or right-click an HTTP(S) video link.');
    return;
  }
  downloading = true;
  try {
    await browser.browserAction.setBadgeText({text: '↓'});
    await browser.browserAction.setTitle({title: transcribe
      ? 'Downloading and transcribing video to Desktop…' : 'Downloading video to Desktop…'});
    let response;
    try {
      response = await browser.runtime.sendNativeMessage('video_downloader', {url, transcribe});
    } catch (error) {
      throw Error('Local helper unavailable. Run install.py from the extension folder. ' + error.message);
    }
    if (!response || !response.ok) throw Error(response?.error || 'No response from downloader.');
    await browser.browserAction.setBadgeText({text: 'OK'});
    const files = [response.path, response.transcript, response.subtitles].filter(Boolean).join('\n');
    await browser.browserAction.setTitle({title: 'Saved: ' + files});
    await notify(transcribe ? 'Video and transcript saved to Desktop' : 'Video saved to Desktop', files);
  } catch (error) {
    await browser.browserAction.setBadgeText({text: '!'});
    await browser.browserAction.setTitle({title: error.message.slice(0, 500)});
    await notify(transcribe ? 'Download or transcription failed' : 'Video download failed', error.message);
  } finally {
    downloading = false;
  }
}

browser.browserAction.onClicked.addListener(tab => download(tab.url));
browser.menus.create({
  id: 'download-video', title: 'Download video to Desktop',
  contexts: ['page', 'link', 'video'],
});
browser.menus.create({
  id: 'transcribe-video', title: 'Download + transcribe to Desktop',
  contexts: ['page', 'link', 'video'],
});
browser.menus.onClicked.addListener((info, tab) => {
  if (!['download-video', 'transcribe-video'].includes(info.menuItemId)) return;
  const source = info.linkUrl || info.srcUrl;
  // Blob URLs exist only inside the page; let yt-dlp extract the page instead.
  const url = source && /^https?:\/\//i.test(source)
    ? source : (info.frameUrl || info.pageUrl || tab?.url);
  return download(url, info.menuItemId === 'transcribe-video');
});
