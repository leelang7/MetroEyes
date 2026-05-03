import 'dart:async';
import 'dart:convert';
import 'dart:io';

class BevPayload {
  final double fps;
  final int frameIdx;
  final List<Map<String, dynamic>> tracks;
  final String? device;
  BevPayload({required this.fps, required this.frameIdx, required this.tracks, this.device});

  factory BevPayload.fromJson(Map<String, dynamic> j) => BevPayload(
        fps: (j['fps'] as num?)?.toDouble() ?? 0.0,
        frameIdx: (j['frame_idx'] as num?)?.toInt() ?? 0,
        tracks: ((j['tracks'] as List?) ?? []).cast<Map<String, dynamic>>(),
        device: j['device']?.toString(),
      );

  int get personCount => tracks.where((t) => t['class'] == 'person').length;
  int get vehicleCount =>
      tracks.where((t) => ['car', 'bus', 'truck'].contains(t['class'])).length;

  /// person 트랙을 bev_x 0~1 구간 기준 [bins]개 칸으로 분할해 카운트.
  /// 카메라 시야 = 편성 1량 통째 가정. bev_x가 누락된 트랙은 무시.
  List<int> personPerBin(int bins) {
    final out = List<int>.filled(bins, 0);
    for (final t in tracks) {
      if (t['class'] != 'person') continue;
      final x = (t['bev_x'] as num?)?.toDouble();
      if (x == null) continue;
      var idx = (x * bins).floor();
      if (idx < 0) idx = 0;
      if (idx >= bins) idx = bins - 1;
      out[idx]++;
    }
    return out;
  }
}

enum SocketState { disconnected, connecting, connected, error }

/// 도시철도 실시간 도착정보 한 행 (서울 열린데이터광장 realtimeStationArrival 정규화).
class ArrivalRow {
  final String? subwayId;     // "1002" = 2호선
  final String? trainLineNm;  // 예: "잠실행 - 잠실(송파나루)방면"
  final String? bstatnNm;     // 종착역
  final String? arvlMsg2;     // 사람 친화 메시지
  final String? arvlMsg3;     // 현재 위치
  final int? arvlCd;          // 1:당역접근 2:전역출발 3:전전역출발 5:당역도착
  final int? barvlDt;         // 도착예정 초
  final String? updnLine;     // 상행/하행
  ArrivalRow({this.subwayId, this.trainLineNm, this.bstatnNm,
      this.arvlMsg2, this.arvlMsg3, this.arvlCd, this.barvlDt, this.updnLine});

  factory ArrivalRow.fromJson(Map<String, dynamic> j) => ArrivalRow(
        subwayId: j['subwayId']?.toString(),
        trainLineNm: j['trainLineNm']?.toString(),
        bstatnNm: j['bstatnNm']?.toString(),
        arvlMsg2: j['arvlMsg2']?.toString(),
        arvlMsg3: j['arvlMsg3']?.toString(),
        arvlCd: int.tryParse(j['arvlCd']?.toString() ?? ''),
        barvlDt: int.tryParse(j['barvlDt']?.toString() ?? ''),
        updnLine: j['updnLine']?.toString(),
      );

  /// 0이면 즉시(당역도착/접근), null이면 미상.
  int? get etaSeconds {
    if (barvlDt != null && barvlDt! > 0) return barvlDt;
    if (arvlCd == 5 || arvlCd == 1) return 0;
    return null;
  }
}

/// 서울 실시간 도시데이터 — POI별 현재 추정 인구 + 혼잡도 레벨.
class PopulationResponse {
  final String poi;
  final String? areaNm;
  final String? areaCd;
  final String? congestLvl;   // 여유 / 보통 / 약간 붐빔 / 붐빔
  final String? congestMsg;
  final int? ppltnMin;
  final int? ppltnMax;
  final double? maleRate, femaleRate;
  final double? resntRate, nonResntRate;
  final String? ppltnTime;
  final String? error;
  PopulationResponse({
    required this.poi,
    this.areaNm,
    this.areaCd,
    this.congestLvl,
    this.congestMsg,
    this.ppltnMin,
    this.ppltnMax,
    this.maleRate,
    this.femaleRate,
    this.resntRate,
    this.nonResntRate,
    this.ppltnTime,
    this.error,
  });

  factory PopulationResponse.fromJson(Map<String, dynamic> j) =>
      PopulationResponse(
        poi: j['poi']?.toString() ?? '',
        areaNm: j['area_nm']?.toString(),
        areaCd: j['area_cd']?.toString(),
        congestLvl: j['congest_lvl']?.toString(),
        congestMsg: j['congest_msg']?.toString(),
        ppltnMin: (j['ppltn_min'] as num?)?.toInt(),
        ppltnMax: (j['ppltn_max'] as num?)?.toInt(),
        maleRate: (j['male_rate'] as num?)?.toDouble(),
        femaleRate: (j['female_rate'] as num?)?.toDouble(),
        resntRate: (j['resnt_rate'] as num?)?.toDouble(),
        nonResntRate: (j['non_resnt_rate'] as num?)?.toDouble(),
        ppltnTime: j['ppltn_time']?.toString(),
        error: j['error']?.toString(),
      );

  /// 추정 인구 중간값 (min/max 평균).
  int? get ppltnMid {
    if (ppltnMin == null && ppltnMax == null) return null;
    if (ppltnMin == null) return ppltnMax;
    if (ppltnMax == null) return ppltnMin;
    return ((ppltnMin! + ppltnMax!) / 2).round();
  }
}

class ArrivalResponse {
  final String station;
  final int? line;
  final List<ArrivalRow> items;
  final String? error;
  /// true이면 backend가 시뮬 fallback 사용 (실제 API 비응답/키 미등록).
  final bool simulated;
  ArrivalResponse({required this.station, this.line, required this.items,
      this.error, this.simulated = false});

  factory ArrivalResponse.fromJson(Map<String, dynamic> j) => ArrivalResponse(
        station: j['station']?.toString() ?? '',
        line: (j['line'] as num?)?.toInt(),
        items: ((j['items'] as List?) ?? [])
            .cast<Map<String, dynamic>>()
            .map(ArrivalRow.fromJson)
            .toList(),
        error: j['error']?.toString(),
        simulated: j['simulated'] == true,
      );
}

class BevSocket {
  WebSocket? _ws;
  final _stateCtrl = StreamController<SocketState>.broadcast();
  final _payloadCtrl = StreamController<BevPayload>.broadcast();
  final _arrivalCtrl = StreamController<ArrivalResponse>.broadcast();
  final _populationCtrl = StreamController<PopulationResponse>.broadcast();
  Timer? _retry;

  Stream<SocketState> get state => _stateCtrl.stream;
  Stream<BevPayload> get payloads => _payloadCtrl.stream;
  Stream<ArrivalResponse> get arrivals => _arrivalCtrl.stream;
  Stream<PopulationResponse> get populations => _populationCtrl.stream;
  SocketState _current = SocketState.disconnected;
  SocketState get current => _current;

  /// 백엔드에 실시간 도착정보 요청. 응답은 [arrivals] stream으로 도착.
  void queryArrival(String stationName, {int? line}) {
    final ws = _ws;
    if (ws == null) return;
    try {
      ws.add(jsonEncode({
        'type': 'arrival_query',
        'stationName': stationName,
        if (line != null) 'line': line,
      }));
    } catch (_) {}
  }

  /// 백엔드에 서울 실시간 도시데이터(POI 인구) 요청. 응답은 [populations] stream으로.
  void queryPopulation(String poi) {
    final ws = _ws;
    if (ws == null) return;
    try {
      ws.add(jsonEncode({'type': 'population_query', 'poi': poi}));
    } catch (_) {}
  }

  void _emit(SocketState s) {
    _current = s;
    _stateCtrl.add(s);
  }

  Future<void> connect(String url) async {
    await disconnect();
    _emit(SocketState.connecting);
    try {
      // ngrok 무료 tier 브라우저 경고 우회
      _ws = await WebSocket.connect(
        url,
        headers: {'ngrok-skip-browser-warning': '1'},
      ).timeout(const Duration(seconds: 8));
      _emit(SocketState.connected);
      _ws!.listen(
        (data) {
          if (data is String) {
            try {
              final j = jsonDecode(data);
              if (j is Map<String, dynamic>) {
                final type = j['type'];
                if (type == 'arrival') {
                  _arrivalCtrl.add(ArrivalResponse.fromJson(j));
                } else if (type == 'population') {
                  _populationCtrl.add(PopulationResponse.fromJson(j));
                } else {
                  _payloadCtrl.add(BevPayload.fromJson(j));
                }
              }
            } catch (_) {}
          }
        },
        onDone: () {
          _emit(SocketState.disconnected);
          _scheduleRetry(url);
        },
        onError: (_) {
          _emit(SocketState.error);
          _scheduleRetry(url);
        },
        cancelOnError: true,
      );
    } catch (e) {
      _emit(SocketState.error);
      _scheduleRetry(url);
    }
  }

  void _scheduleRetry(String url) {
    _retry?.cancel();
    _retry = Timer(const Duration(seconds: 3), () => connect(url));
  }

  Future<void> disconnect() async {
    _retry?.cancel();
    _retry = null;
    final ws = _ws;
    _ws = null;
    if (ws != null) {
      try { await ws.close(); } catch (_) {}
    }
    _emit(SocketState.disconnected);
  }

  void dispose() {
    disconnect();
    _stateCtrl.close();
    _payloadCtrl.close();
    _arrivalCtrl.close();
    _populationCtrl.close();
  }
}
