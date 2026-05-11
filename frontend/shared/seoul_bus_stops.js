// MetroEyes — 서울 주요 버스 정류장 목록
// operator_web/bus.html + passenger_app 공용

window.SEOUL_BUS_STOPS = [
  // ── 강남·서초 ──────────────────────────────────
  { name:'강남역.11번출구',      short:'강남역',       route:'광역 9408', lat:37.4980, lon:127.0276, cluster:'office', poi:'강남역' },
  { name:'강남역.7번출구',       short:'강남역(북)',    route:'간선 146',  lat:37.4999, lon:127.0282, cluster:'office', poi:'강남역' },
  { name:'신논현역.3번출구',     short:'신논현',       route:'간선 461',  lat:37.5045, lon:127.0250, cluster:'office', poi:'신논현·언주' },
  { name:'교대역.7번출구',       short:'교대역',       route:'간선 405',  lat:37.4934, lon:127.0149, cluster:'hub',    poi:'강남·역삼' },
  { name:'역삼역.4번출구',       short:'역삼역',       route:'간선 4212', lat:37.5005, lon:127.0364, cluster:'office', poi:'테헤란로' },
  { name:'선릉역.6번출구',       short:'선릉역',       route:'간선 462',  lat:37.5044, lon:127.0489, cluster:'office', poi:'테헤란로' },
  { name:'삼성역.5번출구',       short:'삼성역',       route:'간선 9호',  lat:37.5085, lon:127.0624, cluster:'office', poi:'코엑스·무역센터' },
  { name:'양재역.3번출구',       short:'양재역',       route:'간선 4429', lat:37.4845, lon:127.0340, cluster:'office', poi:'양재·매봉' },
  { name:'서초역.3번출구',       short:'서초역',       route:'간선 400',  lat:37.4912, lon:127.0082, cluster:'office', poi:'강남·역삼' },
  { name:'고속터미널.경부',      short:'고속터미널',   route:'간선 405',  lat:37.5050, lon:127.0048, cluster:'hub',    poi:'반포한강공원' },

  // ── 잠실·송파 ──────────────────────────────────
  { name:'잠실역.7번출구',       short:'잠실역',       route:'간선 142',  lat:37.5133, lon:127.1003, cluster:'hub',    poi:'잠실역' },
  { name:'잠실역.5번출구',       short:'잠실역(남)',    route:'간선 301',  lat:37.5110, lon:127.0988, cluster:'hub',    poi:'잠실역' },
  { name:'종합운동장.올림픽',     short:'종합운동장',   route:'간선 340',  lat:37.5110, lon:127.0739, cluster:'leisure',poi:'잠실 한강공원' },
  { name:'석촌역.4번출구',       short:'석촌역',       route:'간선 303',  lat:37.5078, lon:127.1026, cluster:'resi',   poi:null },
  { name:'천호역.5번출구',       short:'천호역',       route:'간선 3217', lat:37.5398, lon:127.1236, cluster:'hub',    poi:'천호·성내' },

  // ── 홍대·마포·신촌 ────────────────────────────
  { name:'홍대입구역.9번출구',   short:'홍대입구',     route:'간선 271',  lat:37.5572, lon:126.9244, cluster:'hub',    poi:'홍대 관광특구', hot:true },
  { name:'홍대입구역.2번출구',   short:'홍대입구(공항)', route:'공항 6019', lat:37.5580, lon:126.9265, cluster:'hub',  poi:'홍대 관광특구' },
  { name:'신촌오거리',           short:'신촌',         route:'간선 753',  lat:37.5556, lon:126.9362, cluster:'office', poi:'신촌·이대역' },
  { name:'이대역.3번출구',       short:'이대역',       route:'간선 7016', lat:37.5568, lon:126.9457, cluster:'resi',   poi:'신촌·이대역' },
  { name:'합정역.1번출구',       short:'합정역',       route:'간선 604',  lat:37.5497, lon:126.9147, cluster:'hub',    poi:'합정·당인리' },
  { name:'공덕역.6번출구',       short:'공덕역',       route:'간선 463',  lat:37.5438, lon:126.9516, cluster:'hub',    poi:'공덕·마포' },
  { name:'마포역.1번출구',       short:'마포역',       route:'간선 600',  lat:37.5440, lon:126.9516, cluster:'resi',   poi:'공덕·마포' },

  // ── 여의도 ──────────────────────────────────────
  { name:'여의도역.3번출구',     short:'여의도역',     route:'간선 362',  lat:37.5217, lon:126.9244, cluster:'office', poi:'여의도·한강공원' },
  { name:'여의도환승센터',       short:'여의도환승',   route:'광역 1002', lat:37.5238, lon:126.9263, cluster:'hub',    poi:'여의도·한강공원' },
  { name:'국회의사당.앞',        short:'국회의사당',   route:'간선 160',  lat:37.5298, lon:126.9147, cluster:'office', poi:'여의도·한강공원' },

  // ── 시청·광화문·종로 ──────────────────────────
  { name:'시청역.6번출구',       short:'시청',         route:'간선 162',  lat:37.5642, lon:126.9778, cluster:'office', poi:'광화문·덕수궁' },
  { name:'광화문.교보문고',      short:'광화문',       route:'간선 401',  lat:37.5717, lon:126.9766, cluster:'office', poi:'광화문·덕수궁' },
  { name:'종로3가역.5번출구',    short:'종로3가',      route:'간선 103',  lat:37.5717, lon:126.9914, cluster:'hub',    poi:'종로·청계 관광특구' },
  { name:'동대문역사문화공원.앞', short:'동대문DDP',    route:'간선 301',  lat:37.5665, lon:127.0091, cluster:'hub',    poi:'동대문 관광특구', hot:true },
  { name:'명동역.4번출구',       short:'명동역',       route:'간선 421',  lat:37.5635, lon:126.9831, cluster:'hub',    poi:'명동 관광특구' },

  // ── 서울역·용산 ───────────────────────────────
  { name:'서울역.버스환승',      short:'서울역',       route:'광역 9714', lat:37.5547, lon:126.9707, cluster:'hub',    poi:'서울역' },
  { name:'서울역.서부',          short:'서울역(서)',    route:'간선 150',  lat:37.5530, lon:126.9647, cluster:'hub',    poi:'서울역' },
  { name:'용산역.앞',            short:'용산역',       route:'간선 151',  lat:37.5299, lon:126.9648, cluster:'hub',    poi:'용산 관광특구' },
  { name:'이태원역.2번출구',     short:'이태원',       route:'간선 421',  lat:37.5345, lon:126.9943, cluster:'hub',    poi:'이태원 관광특구', hot:true },

  // ── 강동·하남 ─────────────────────────────────
  { name:'강동역.4번출구',       short:'강동역',       route:'간선 3217', lat:37.5304, lon:127.1352, cluster:'hub',    poi:null },
  { name:'천호역.8번출구',       short:'천호(동)',     route:'간선 320',  lat:37.5390, lon:127.1270, cluster:'hub',    poi:'천호·성내' },

  // ── 노원·도봉·강북 ────────────────────────────
  { name:'노원역.3번출구',       short:'노원역',       route:'간선 1124', lat:37.6543, lon:127.0617, cluster:'hub',    poi:'노원역' },
  { name:'창동역.4번출구',       short:'창동역',       route:'간선 1101', lat:37.6527, lon:127.0478, cluster:'hub',    poi:null },
  { name:'수유역.4번출구',       short:'수유역',       route:'간선 120',  lat:37.6377, lon:127.0253, cluster:'hub',    poi:null },

  // ── 성수·뚝섬 핫스팟 ─────────────────────────
  { name:'성수카페거리',         short:'성수',         route:'간선 121',  lat:37.5444, lon:127.0557, cluster:'hub',    poi:'성수카페거리', hot:true },
  { name:'서울숲.거꾸로분수',    short:'서울숲',       route:'지선 2014', lat:37.5443, lon:127.0374, cluster:'leisure',poi:'서울숲공원',   hot:true },
  { name:'뚝섬한강공원',         short:'뚝섬',         route:'간선 410',  lat:37.5295, lon:127.0708, cluster:'leisure',poi:'뚝섬한강공원', hot:true },
  { name:'건대입구역.6번출구',   short:'건대입구',     route:'간선 240',  lat:37.5403, lon:127.0703, cluster:'resi',   poi:'건대입구역' },

  // ── 사당·방배·동작 ────────────────────────────
  { name:'사당역.4번출구',       short:'사당역',       route:'간선 4318', lat:37.4766, lon:126.9817, cluster:'hub',    poi:'사당역' },
  { name:'동작역.3번출구',       short:'동작역',       route:'간선 752',  lat:37.5031, lon:126.9798, cluster:'hub',    poi:null },
  { name:'이수역.앞',            short:'이수역',       route:'간선 6515', lat:37.4867, lon:126.9815, cluster:'hub',    poi:null },

  // ── 영등포·구로 ───────────────────────────────
  { name:'영등포역.6번출구',     short:'영등포역',     route:'간선 5714', lat:37.5159, lon:126.9070, cluster:'hub',    poi:'영등포 타임스퀘어' },
  { name:'신도림역.3번출구',     short:'신도림역',     route:'간선 601',  lat:37.5083, lon:126.8912, cluster:'hub',    poi:null },
  { name:'구로역.2번출구',       short:'구로역',       route:'간선 504',  lat:37.5025, lon:126.8817, cluster:'hub',    poi:null },
  { name:'가산디지털단지역.앞',  short:'가산단지',     route:'간선 5528', lat:37.4795, lon:126.8821, cluster:'office', poi:null },

  // ── DMC·마곡 ──────────────────────────────────
  { name:'디지털미디어시티역.앞', short:'DMC역',        route:'간선 571',  lat:37.5772, lon:126.8906, cluster:'office', poi:'DMC·마곡' },
  { name:'마곡나루역.1번출구',   short:'마곡나루',     route:'간선 6645', lat:37.5573, lon:126.8254, cluster:'office', poi:'마곡·공항지구' },
  { name:'목동역.4번출구',       short:'목동역',       route:'간선 6630', lat:37.5258, lon:126.8748, cluster:'hub',    poi:'목동' },

  // ── 연신내·은평 ───────────────────────────────
  { name:'연신내역.5번출구',     short:'연신내역',     route:'간선 701',  lat:37.6191, lon:126.9210, cluster:'hub',    poi:'은평·연신내' },
  { name:'불광역.3번출구',       short:'불광역',       route:'간선 702',  lat:37.6095, lon:126.9296, cluster:'resi',   poi:null },

  // ── 공항 ──────────────────────────────────────
  { name:'김포공항.국내선',      short:'김포공항',     route:'광역 6030', lat:37.5615, lon:126.8014, cluster:'hub',    poi:'김포공항' },
];
