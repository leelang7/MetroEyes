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

/// citydata 통합 응답 (날씨/공기/UV/주차/따릉이/도로/24h 예보/상권/안전).
class CitydataResponse {
  final String poi;
  // 인구·혼잡 (citydata_ppltn과 중복)
  final String? areaNm;
  final String? congestLvl;
  final int? ppltnMin, ppltnMax;
  final String? ppltnTime;
  // 날씨
  final double? temp, sensibleTemp, humidity;
  final String? precptType, pcpMsg;
  // 공기질
  final int? pm25, pm10;
  final String? pm25Idx, pm10Idx, airIdx, airMsg;
  // 자외선
  final int? uvLvl;
  final String? uvIdx, uvMsg;
  // 강수 예보 첫 시각
  final String? rainFirstDt;
  final String? rainFirstType;
  // 도로
  final double? roadAvgSpeed;
  final String? roadAvgIdx, roadMsg;
  // 환승 옵션 합계
  final int sbikeSharedTotal;
  final int parkingAvailTotal;
  // 안전
  final List<dynamic> events;
  final List<dynamic> alerts;
  final List<dynamic> accidents;
  final String? error;

  CitydataResponse({
    required this.poi,
    this.areaNm, this.congestLvl, this.ppltnMin, this.ppltnMax, this.ppltnTime,
    this.temp, this.sensibleTemp, this.humidity, this.precptType, this.pcpMsg,
    this.pm25, this.pm10, this.pm25Idx, this.pm10Idx, this.airIdx, this.airMsg,
    this.uvLvl, this.uvIdx, this.uvMsg,
    this.rainFirstDt, this.rainFirstType,
    this.roadAvgSpeed, this.roadAvgIdx, this.roadMsg,
    this.sbikeSharedTotal = 0, this.parkingAvailTotal = 0,
    this.events = const [], this.alerts = const [], this.accidents = const [],
    this.error,
  });

  factory CitydataResponse.fromJson(Map<String, dynamic> j) {
    final sbike = (j['sbike'] as List?) ?? const [];
    final parking = (j['parking'] as List?) ?? const [];
    final rainFirst = j['rain_first'] as Map<String, dynamic>?;
    int sbikeShared = 0;
    for (final s in sbike) {
      if (s is Map && s['shared'] is num) sbikeShared += (s['shared'] as num).toInt();
    }
    int prkAvail = 0;
    for (final p in parking) {
      if (p is Map) {
        final cap = (p['cap'] as num?)?.toInt() ?? 0;
        final cur = (p['cur'] as num?)?.toInt() ?? 0;
        if (cap > cur) prkAvail += (cap - cur);
      }
    }
    return CitydataResponse(
      poi: j['poi']?.toString() ?? '',
      areaNm: j['area_nm']?.toString(),
      congestLvl: j['congest_lvl']?.toString(),
      ppltnMin: (j['ppltn_min'] as num?)?.toInt(),
      ppltnMax: (j['ppltn_max'] as num?)?.toInt(),
      ppltnTime: j['ppltn_time']?.toString(),
      temp: (j['temp'] as num?)?.toDouble(),
      sensibleTemp: (j['sensible_temp'] as num?)?.toDouble(),
      humidity: (j['humidity'] as num?)?.toDouble(),
      precptType: j['precpt_type']?.toString(),
      pcpMsg: j['pcp_msg']?.toString(),
      pm25: (j['pm25'] as num?)?.toInt(),
      pm10: (j['pm10'] as num?)?.toInt(),
      pm25Idx: j['pm25_idx']?.toString(),
      pm10Idx: j['pm10_idx']?.toString(),
      airIdx: j['air_idx']?.toString(),
      airMsg: j['air_msg']?.toString(),
      uvLvl: (j['uv_lvl'] as num?)?.toInt(),
      uvIdx: j['uv_idx']?.toString(),
      uvMsg: j['uv_msg']?.toString(),
      rainFirstDt: rainFirst?['dt']?.toString(),
      rainFirstType: rainFirst?['type']?.toString(),
      roadAvgSpeed: (j['road_avg_speed'] as num?)?.toDouble(),
      roadAvgIdx: j['road_avg_idx']?.toString(),
      roadMsg: j['road_msg']?.toString(),
      sbikeSharedTotal: sbikeShared,
      parkingAvailTotal: prkAvail,
      events: (j['events'] as List?) ?? const [],
      alerts: (j['alerts'] as List?) ?? const [],
      accidents: (j['accidents'] as List?) ?? const [],
      error: j['error']?.toString(),
    );
  }
}

/// 행사 1건.
class EventItem {
  final String? name;
  final String? place;
  final int? vMax;
  final double? distKm;
  EventItem({this.name, this.place, this.vMax, this.distKm});
  factory EventItem.fromJson(Map<String, dynamic> j) => EventItem(
        name: j['name']?.toString(),
        place: j['place']?.toString(),
        vMax: (j['v_max'] as num?)?.toInt(),
        distKm: (j['dist_km'] as num?)?.toDouble(),
      );
}

class EventsResponse {
  final String poi;
  final List<EventItem> events;
  final int totalCount;
  final int totalCapacity;
  final String? error;
  EventsResponse({required this.poi, required this.events, this.totalCount = 0, this.totalCapacity = 0, this.error});
  factory EventsResponse.fromJson(Map<String, dynamic> j) => EventsResponse(
        poi: j['poi']?.toString() ?? '',
        events: ((j['events'] as List?) ?? const [])
            .cast<Map<String, dynamic>>()
            .map(EventItem.fromJson)
            .toList(),
        totalCount: (j['total_count'] as num?)?.toInt() ?? 0,
        totalCapacity: (j['total_capacity'] as num?)?.toInt() ?? 0,
        error: j['error']?.toString(),
      );
}

/// 사회적 임팩트 누적.
class ImpactSummary {
  final int totalCount;
  final double avgSavedPct;
  ImpactSummary({this.totalCount = 0, this.avgSavedPct = 0});
  factory ImpactSummary.fromJson(Map<String, dynamic> j) => ImpactSummary(
        totalCount: (j['total_count'] as num?)?.toInt() ?? 0,
        avgSavedPct: (j['avg_saved_pct'] as num?)?.toDouble() ?? 0,
      );
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
  final _citydataCtrl = StreamController<CitydataResponse>.broadcast();
  final _eventsCtrl = StreamController<EventsResponse>.broadcast();
  final _impactCtrl = StreamController<ImpactSummary>.broadcast();
  Timer? _retry;

  Stream<SocketState> get state => _stateCtrl.stream;
  Stream<BevPayload> get payloads => _payloadCtrl.stream;
  Stream<ArrivalResponse> get arrivals => _arrivalCtrl.stream;
  Stream<PopulationResponse> get populations => _populationCtrl.stream;
  Stream<CitydataResponse> get citydatas => _citydataCtrl.stream;
  Stream<EventsResponse> get events => _eventsCtrl.stream;
  Stream<ImpactSummary> get impacts => _impactCtrl.stream;
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
    try { ws.add(jsonEncode({'type': 'population_query', 'poi': poi})); } catch (_) {}
  }

  /// citydata 통합 (날씨/공기/도로/환승). 응답은 [citydatas] stream.
  void queryCitydata(String poi) {
    final ws = _ws;
    if (ws == null) return;
    try { ws.add(jsonEncode({'type': 'citydata_query', 'poi': poi})); } catch (_) {}
  }

  /// 주변 행사 (인구 영향 신호). 응답은 [events] stream.
  void queryEvents(String poi) {
    final ws = _ws;
    if (ws == null) return;
    try { ws.add(jsonEncode({'type': 'events_query', 'poi': poi})); } catch (_) {}
  }

  /// 사회적 임팩트 로그 — 추천 칸 탑승 시 호출. 백엔드가 broadcast한 [impacts]를 모든 client가 받음.
  void logImpact({required String station, required String car, required int savedPct}) {
    final ws = _ws;
    if (ws == null) return;
    try {
      ws.add(jsonEncode({
        'type': 'impact_log', 'station': station, 'car': car, 'saved_pct': savedPct,
      }));
    } catch (_) {}
  }

  /// IDEA-1 Phone-as-Sensor — 익명 폰 텔레메트리 송신.
  ///
  /// 진동 강도(ax/ay/az 가속도 norm)·움직임 빈도·근접 BLE 핑 카운트를
  /// 익명 집계로 백엔드에 전송. 백엔드는 동일 station 의 다수 폰 신호를
  /// 합산해 칸별 점유 추정의 weak signal 로 사용.
  ///
  /// 진짜 sensors_plus + flutter_blue_plus 통합은 후속. 현 stub 은 송신 채널만.
  /// 프라이버시: 개인 ID 없음, 가속도 raw 값 자체도 안 보내고 norm 만.
  void sendPhoneTelemetry({
    required String station,
    required double accelMagnitude, // sqrt(ax^2+ay^2+az^2) - 9.8 (정지 시 0)
    int? bleNearbyCount,
    int? wifiProbeRssiMean,
  }) {
    final ws = _ws;
    if (ws == null) return;
    try {
      ws.add(jsonEncode({
        'type': 'phone_telemetry',
        'station': station,
        'accel_mag': accelMagnitude,
        if (bleNearbyCount != null) 'ble_count': bleNearbyCount,
        if (wifiProbeRssiMean != null) 'wifi_rssi_mean': wifiProbeRssiMean,
        'ts_ms': DateTime.now().millisecondsSinceEpoch,
      }));
    } catch (_) {}
  }

  void citizenReport({required String incidentType, required String station}) {
    final ws = _ws;
    if (ws == null) return;
    try {
      ws.add(jsonEncode({
        'type': 'citizen_report',
        'incident_type': incidentType,
        'station': station,
        'source': 'flutter-app',
        'ts': DateTime.now().millisecondsSinceEpoch / 1000.0,
      }));
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
                } else if (type == 'citydata') {
                  _citydataCtrl.add(CitydataResponse.fromJson(j));
                } else if (type == 'events') {
                  _eventsCtrl.add(EventsResponse.fromJson(j));
                } else if (type == 'impact_summary') {
                  _impactCtrl.add(ImpactSummary.fromJson(j));
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
    _citydataCtrl.close();
    _eventsCtrl.close();
    _impactCtrl.close();
  }
}
