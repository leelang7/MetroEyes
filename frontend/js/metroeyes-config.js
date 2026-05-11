/* MetroEyes — 백엔드 URL 환경 자동 감지 (cycle 539)
 * 로컬: localhost:8765 / 클라우드: app.allthatai.kr / GitHub Pages: app.allthatai.kr
 */
(function () {
  var h = location.hostname;
  var remote = location.protocol === 'https:' || h.endsWith('github.io') || h === 'app.allthatai.kr';
  window.METROEYES_BACKEND = remote ? 'https://app.allthatai.kr' : 'http://localhost:8765';
  window.METROEYES_WS      = remote ? 'wss://app.allthatai.kr'   : 'ws://localhost:8765';
})();
