import 'dart:async';
import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'bev_socket.dart';

class StationCoord {
  final String name;
  final int line;
  final double lat;
  final double lon;
  /// 서울 실시간 도시데이터 POI명 (citydata_ppltn 인자). null이면 인구 표시 생략.
  final String? populationPoi;
  const StationCoord(this.name, this.line, this.lat, this.lon, {this.populationPoi});
}

// 시연/매칭용 주요 역. populationPoi는 서울 110개 핫스팟 중 가까운 곳.
const _stations = <StationCoord>[
  StationCoord('잠실', 2, 37.5133, 127.1000, populationPoi: '잠실역'),
  StationCoord('강남', 2, 37.4980, 127.0276, populationPoi: '강남역'),
  StationCoord('홍대입구', 2, 37.5572, 126.9244, populationPoi: '홍대 관광특구'),
  StationCoord('시청', 2, 37.5642, 126.9778, populationPoi: '광화문·덕수궁'),
  StationCoord('서울역', 1, 37.5547, 126.9707, populationPoi: '서울역'),
  StationCoord('광화문', 5, 37.5717, 126.9766, populationPoi: '광화문·덕수궁'),
  StationCoord('종로3가', 1, 37.5717, 126.9914, populationPoi: '종로·청계 관광특구'),
  StationCoord('신촌', 2, 37.5556, 126.9362, populationPoi: '신촌·이대역'),
  StationCoord('사당', 2, 37.4766, 126.9817, populationPoi: '사당역'),
  StationCoord('건대입구', 2, 37.5403, 127.0703, populationPoi: '건대입구역'),
  StationCoord('노원', 4, 37.6543, 127.0617),
  StationCoord('김포공항', 5, 37.5615, 126.8014, populationPoi: '김포공항'),
];

double _haversineKm(double lat1, double lon1, double lat2, double lon2) {
  const r = 6371.0;
  final dLat = (lat2 - lat1) * math.pi / 180;
  final dLon = (lon2 - lon1) * math.pi / 180;
  final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
      math.cos(lat1 * math.pi / 180) *
          math.cos(lat2 * math.pi / 180) *
          math.sin(dLon / 2) *
          math.sin(dLon / 2);
  return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
}

({StationCoord station, double km}) _nearestStation(double lat, double lon) {
  StationCoord best = _stations.first;
  double bestKm = double.infinity;
  for (final s in _stations) {
    final d = _haversineKm(lat, lon, s.lat, s.lon);
    if (d < bestKm) {
      bestKm = d;
      best = s;
    }
  }
  return (station: best, km: bestKm);
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Color(0xFF04060A),
    statusBarIconBrightness: Brightness.light,
    systemNavigationBarColor: Color(0xFF04060A),
  ));
  runApp(const MetroEyesApp());
}

// ============== 디자인 토큰 ==============
const _bg = Color(0xFF04060A);
const _panel = Color(0xFF0A0D14);
const _line = Color(0x12FFFFFF);
const _line2 = Color(0x24FFFFFF);
const _fg = Color(0xFFE8EDF5);
const _muted = Color(0xFF6B768A);
const _muted2 = Color(0xFF8E98AC);
const _accent = Color(0xFF7DD3D3);
const _accentSoft = Color(0x1A7DD3D3);
const _warn = Color(0xFFF0B46A);
const _crit = Color(0xFFFF5E57);

// ============== 도메인 모델 ==============
class Cluster {
  final double am, pm, base;
  final String label;
  const Cluster(this.am, this.pm, this.base, this.label);
}

const _clusters = {
  'office': Cluster(0.32, 0.95, 0.22, '오피스형'),
  'resi': Cluster(0.95, 0.45, 0.22, '주거형'),
  'hub': Cluster(0.85, 0.92, 0.40, '환승 허브'),
};

double _gauss(double x, double mu, double s) =>
    math.exp(-0.5 * math.pow((x - mu) / s, 2).toDouble());

double trainOccupancy(int hour, String clusterId) {
  final c = _clusters[clusterId]!;
  return math.min(1.05,
      c.am * _gauss(hour.toDouble(), 8, 1.0) +
          c.pm * _gauss(hour.toDouble(), 18, 1.2) +
          c.base * _gauss(hour.toDouble(), 13, 4) * 0.4);
}

List<double> carOccupancies(double avg, int n, int seed) {
  final rng = math.Random(seed);
  final out = <double>[];
  for (var i = 0; i < n; i++) {
    final dist = (i - (n - 1) / 2).abs() / ((n - 1) / 2);
    final noise = (rng.nextDouble() - 0.5) * 0.18;
    out.add(math.max(0, math.min(1.1, avg * (1 - dist * 0.55) + noise)));
  }
  return out;
}

/// 라이브 BEV 페이로드 → 칸별 점유율(0~1).
/// 분포는 실 검출(person bev_x 분포), 절대값은 칸당 정원으로 정규화.
/// [capacityPerCar]: 카메라 한 화각이 1칸이라 가정했을 때 정원 (만석 기준).
List<double> liveCarOccupancies(BevPayload p, int n, {int capacityPerCar = 20}) {
  final bins = p.personPerBin(n);
  return [
    for (final c in bins) math.max(0.0, math.min(1.05, c / capacityPerCar))
  ];
}

class Option {
  final int idx;
  final String label;
  final double occ;
  final int etaSeconds;
  Option(this.idx, this.label, this.occ, this.etaSeconds);
}

enum VehicleMode { subway, bus }

// ============== App ==============
class MetroEyesApp extends StatelessWidget {
  const MetroEyesApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MetroEyes',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: _bg,
        useMaterial3: true,
        colorScheme: const ColorScheme.dark(
          primary: _accent,
          surface: _panel,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  VehicleMode _mode = VehicleMode.subway;
  int _hour = 18;
  bool _a11y = false;

  List<Option> _options = [];
  int _selected = 0;

  // 백엔드 라이브 연결 (Cloudflare 터널 — 외부 노출 고정 도메인)
  final BevSocket _bev = BevSocket();
  String _wsUrl = 'wss://app.allthatai.kr';
  SocketState _wsState = SocketState.disconnected;
  BevPayload? _livePayload;
  ArrivalResponse? _arrivals;
  PopulationResponse? _population;
  CitydataResponse? _citydata;
  EventsResponse? _events;
  ImpactSummary? _impact;
  Timer? _arrivalPoll;
  Timer? _populationPoll;
  Timer? _citydataPoll;
  Timer? _eventsPoll;
  Timer? _telemetryTimer;       // IDEA-1 phone-as-sensor 5초 주기
  int _telemetrySent = 0;        // 송신 누적 카운트 (헤더 표시용)
  StreamSubscription? _stateSub;
  StreamSubscription? _payloadSub;
  StreamSubscription? _arrivalSub;
  StreamSubscription? _populationSub;
  StreamSubscription? _citydataSub;
  StreamSubscription? _eventsSub;
  StreamSubscription? _impactSub;

  // 현재 선택된 역 (GPS 매칭 결과로 갱신).
  String _stationName = '잠실';
  int _stationLine = 2;
  String? _stationPoi = '잠실역';   // 서울 실시간 도시데이터 POI명
  double? _stationDistKm;     // GPS와 가장 가까운 역 거리(km)

  @override
  void initState() {
    super.initState();
    _rebuild();
    _stateSub = _bev.state.listen((s) {
      if (mounted) setState(() => _wsState = s);
      if (s == SocketState.connected) {
        // 도착정보: 즉시 + 20초 폴링
        _bev.queryArrival(_stationName, line: _stationLine);
        _arrivalPoll?.cancel();
        _arrivalPoll = Timer.periodic(const Duration(seconds: 20),
            (_) => _bev.queryArrival(_stationName, line: _stationLine));
        // 역세권 인구: 즉시 + 60초 폴링
        if (_stationPoi != null) _bev.queryPopulation(_stationPoi!);
        _populationPoll?.cancel();
        _populationPoll = Timer.periodic(const Duration(seconds: 60), (_) {
          if (_stationPoi != null) _bev.queryPopulation(_stationPoi!);
        });
        // 통합 도시데이터(날씨/공기/도로/따릉이/주차): 즉시 + 60초
        if (_stationPoi != null) _bev.queryCitydata(_stationPoi!);
        _citydataPoll?.cancel();
        _citydataPoll = Timer.periodic(const Duration(seconds: 60), (_) {
          if (_stationPoi != null) _bev.queryCitydata(_stationPoi!);
        });
        // 행사/문화: 즉시 + 10분
        if (_stationPoi != null) _bev.queryEvents(_stationPoi!);
        _eventsPoll?.cancel();
        _eventsPoll = Timer.periodic(const Duration(minutes: 10), (_) {
          if (_stationPoi != null) _bev.queryEvents(_stationPoi!);
        });
        // IDEA-1 Phone-as-Sensor: 5초 주기 익명 텔레메트리 송신.
        // 진짜 sensors_plus 통합 전 stub — 가속도/BLE 시뮬값.
        // 발표 메시지: "사용자가 늘수록 칸 추정 정확도 ↑" 의 채널만 입증.
        _telemetryTimer?.cancel();
        _telemetryTimer = Timer.periodic(const Duration(seconds: 5), (_) {
          // 가속도 norm: 출퇴근 시간 0.3~1.5 (활동), 야간 0.0~0.2 (정지)
          final h = DateTime.now().hour;
          final isPeak = (h >= 7 && h <= 10) || (h >= 17 && h <= 20);
          final base = isPeak ? 0.6 : 0.05;
          final noise = (math.Random().nextDouble() - 0.5) * 0.4;
          final accel = math.max(0.0, base + noise);
          final ble = isPeak ? (8 + math.Random().nextInt(15)) : math.Random().nextInt(4);
          _bev.sendPhoneTelemetry(
            station: _stationName,
            accelMagnitude: accel,
            bleNearbyCount: ble,
          );
          if (mounted) setState(() => _telemetrySent++);
        });
      } else {
        _arrivalPoll?.cancel();
        _arrivalPoll = null;
        _populationPoll?.cancel();
        _populationPoll = null;
        _citydataPoll?.cancel();
        _citydataPoll = null;
        _eventsPoll?.cancel();
        _eventsPoll = null;
        _telemetryTimer?.cancel();
        _telemetryTimer = null;
      }
    });
    _payloadSub = _bev.payloads.listen((p) {
      if (mounted) {
        setState(() {
          _livePayload = p;
          _rebuild();
        });
      }
    });
    _arrivalSub = _bev.arrivals.listen((a) {
      if (mounted) {
        setState(() {
          _arrivals = a;
          _rebuild();
        });
      }
    });
    _populationSub = _bev.populations.listen((p) {
      if (mounted) setState(() => _population = p);
    });
    _citydataSub = _bev.citydatas.listen((c) {
      if (mounted) setState(() => _citydata = c);
    });
    _eventsSub = _bev.events.listen((e) {
      if (mounted) setState(() => _events = e);
    });
    _impactSub = _bev.impacts.listen((i) {
      if (mounted) setState(() => _impact = i);
    });
    // 자동 연결 시도 (USB adb reverse 가정)
    Future.delayed(const Duration(milliseconds: 500), () => _bev.connect(_wsUrl));
    // GPS 권한 요청 + 가장 가까운 역 매칭 (실패해도 잠실 fallback 유지)
    _resolveStationByGps();
  }

  Future<void> _resolveStationByGps() async {
    try {
      if (!await Geolocator.isLocationServiceEnabled()) return;
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) {
        return;
      }
      // 1) 캐시된 마지막 위치 즉시 사용 (있으면 빠르게 매칭)
      Position? pos;
      try {
        pos = await Geolocator.getLastKnownPosition();
      } catch (_) {}
      // 2) 캐시 없거나 너무 오래된 경우만 새 fix 시도
      if (pos == null) {
        try {
          pos = await Geolocator.getCurrentPosition(
            desiredAccuracy: LocationAccuracy.medium,
            timeLimit: const Duration(seconds: 20),
          );
        } catch (_) {}
      }
      if (pos == null) return;
      final r = _nearestStation(pos.latitude, pos.longitude);
      if (!mounted) return;
      setState(() {
        _stationName = r.station.name;
        _stationLine = r.station.line;
        _stationPoi = r.station.populationPoi;
        _stationDistKm = r.km;
        _population = null; // 이전 역 인구 무효화
      });
      _refetchForStation();
    } catch (_) {
      // 무시: 잠실 fallback 유지
    }
  }

  /// station 변경 시 (GPS 또는 수동 선택) 모든 query 재호출.
  void _refetchForStation() {
    if (_wsState != SocketState.connected) return;
    _bev.queryArrival(_stationName, line: _stationLine);
    if (_stationPoi != null) {
      _bev.queryPopulation(_stationPoi!);
      _bev.queryCitydata(_stationPoi!);
      _bev.queryEvents(_stationPoi!);
    }
  }

  /// 수동 station picker — 12개 역 list에서 선택.
  Future<void> _showStationPicker() async {
    final picked = await showModalBottomSheet<StationCoord>(
      context: context,
      backgroundColor: _panel,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 6),
              child: Row(
                children: [
                  const Text('역 선택',
                      style: TextStyle(color: _muted, fontSize: 11, letterSpacing: 1.2)),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: () {
                      Navigator.pop(ctx);
                      _resolveStationByGps();
                    },
                    icon: const Icon(Icons.my_location_rounded, color: _accent, size: 14),
                    label: const Text('GPS 재시도',
                        style: TextStyle(color: _accent, fontSize: 12)),
                  ),
                ],
              ),
            ),
            Flexible(
              child: ListView(
                shrinkWrap: true,
                children: [
                  for (final s in _stations)
                    ListTile(
                      onTap: () => Navigator.pop(ctx, s),
                      leading: Icon(
                        s.name == _stationName
                            ? Icons.radio_button_checked
                            : Icons.radio_button_unchecked,
                        color: s.name == _stationName ? _accent : _muted,
                        size: 18,
                      ),
                      title: Text('${s.name}역',
                          style: TextStyle(
                              color: s.name == _stationName ? _accent : _fg,
                              fontSize: 14,
                              fontWeight: FontWeight.w500)),
                      subtitle: Text(
                          '${s.line}호선 · ${s.populationPoi ?? "POI 없음"}',
                          style: const TextStyle(color: _muted, fontSize: 11)),
                      dense: true,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
    if (picked != null && picked.name != _stationName) {
      setState(() {
        _stationName = picked.name;
        _stationLine = picked.line;
        _stationPoi = picked.populationPoi;
        _stationDistKm = null;
        _population = null;
        _arrivals = null;
        _citydata = null;
        _events = null;
      });
      _refetchForStation();
    }
  }

  @override
  void dispose() {
    _stateSub?.cancel();
    _payloadSub?.cancel();
    _arrivalSub?.cancel();
    _populationSub?.cancel();
    _citydataSub?.cancel();
    _eventsSub?.cancel();
    _impactSub?.cancel();
    _arrivalPoll?.cancel();
    _populationPoll?.cancel();
    _citydataPoll?.cancel();
    _eventsPoll?.cancel();
    _telemetryTimer?.cancel();
    _bev.dispose();
    super.dispose();
  }

  void _rebuild() {
    final avg = trainOccupancy(_hour, 'hub');
    if (_mode == VehicleMode.subway) {
      // 라이브 페이로드가 있으면 person 검출 분포로, 없으면 가우시안 시뮬.
      final live = _livePayload;
      final occs = (live != null && live.personCount > 0)
          ? liveCarOccupancies(live, 10)
          : carOccupancies(avg, 10, _hour * 13 + 7);
      // 라이브 도착정보가 있으면 가장 빠른 차편 ETA를 모든 칸에 동일 적용.
      final liveEta = _firstArrivalSeconds();
      _options = List.generate(10, (i) {
        final eta = liveEta ?? (70 + i);
        return Option(i, '${i + 1}호차', occs[i], eta);
      });
    } else {
      final rng = math.Random(_hour * 17 + 3);
      // 라이브 차량 검출이 있으면 도착 차량 혼잡도에 가중. (카메라 시야 ≒ 정류장).
      final live = _livePayload;
      final liveAvg = (live != null && live.personCount > 0)
          ? math.min(1.05, live.personCount / 30.0) // 정류장 정원 30명 기준
          : null;
      _options = List.generate(3, (i) {
        final noise = (rng.nextDouble() - 0.5) * 0.20;
        final base = liveAvg ?? (avg * 0.92);
        // 1순위는 라이브 그대로, 2~3순위는 시뮬 분산
        final occ = i == 0 && liveAvg != null
            ? math.max(0.05, math.min(1.05, liveAvg + noise * 0.3))
            : math.max(0.05, math.min(1.05, base + noise));
        final eta = i == 0
            ? math.max(60, (rng.nextDouble() * 180).toInt())
            : ((i + 1) * 240 + (rng.nextDouble() * 120)).toInt();
        return Option(i, '${i + 1}순위 차량', occ, eta);
      });
    }
    var bi = 0;
    for (var i = 1; i < _options.length; i++) {
      if (_options[i].occ < _options[bi].occ) bi = i;
    }
    _selected = bi;
  }

  String get _ctxName => _mode == VehicleMode.subway
      ? '$_stationName역'
      : '$_stationName역.7번출구';
  String get _ctxLine {
    if (_mode != VehicleMode.subway) return '간선 142';
    // 라이브 도착정보의 첫 행 trainLineNm을 활용하면 더 풍부.
    final first = _arrivals?.items.isNotEmpty == true ? _arrivals!.items.first : null;
    final dest = first?.bstatnNm;
    return dest != null && dest.isNotEmpty
        ? '$_stationLine호선 · $dest행'
        : '$_stationLine호선';
  }

  String _liveClock() {
    final n = DateTime.now();
    final hh = n.hour.toString().padLeft(2, '0');
    final mm = n.minute.toString().padLeft(2, '0');
    return '$hh:$mm';
  }

  /// 가장 빠른 도착 차편의 ETA(초). 라이브 응답 없거나 비면 null.
  int? _firstArrivalSeconds() {
    final items = _arrivals?.items;
    if (items == null || items.isEmpty) return null;
    int? best;
    for (final r in items) {
      final s = r.etaSeconds;
      if (s == null) continue;
      if (best == null || s < best) best = s;
    }
    return best;
  }

  void _showReportDialog() {
    final types = [
      {'type': 'emergency', 'icon': '🚨', 'label': '응급 신고', 'color': const Color(0xFFEF4444)},
      {'type': 'lost',      'icon': '🎒', 'label': '분실물 신고', 'color': const Color(0xFFF59E0B)},
      {'type': 'priority_seat', 'icon': '♿', 'label': '배려석 요청', 'color': const Color(0xFFA855F7)},
    ];
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('시민 신고', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text('$_stationName · 운영자 콘솔 즉시 전달', style: const TextStyle(color: _muted, fontSize: 12)),
            const SizedBox(height: 16),
            ...types.map((t) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: (t['color'] as Color).withValues(alpha: 0.15),
                  foregroundColor: t['color'] as Color,
                  side: BorderSide(color: (t['color'] as Color).withValues(alpha: 0.5)),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                icon: Text(t['icon'] as String, style: const TextStyle(fontSize: 18)),
                label: Text(t['label'] as String, style: const TextStyle(fontWeight: FontWeight.w700)),
                onPressed: () {
                  _bev.citizenReport(incidentType: t['type'] as String, station: _stationName);
                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('${t["icon"]} ${t["label"]} 전송 완료'),
                      backgroundColor: t['color'] as Color,
                      duration: const Duration(seconds: 2),
                    ),
                  );
                },
              ),
            )),
          ],
        ),
      ),
    );
  }

  void _showSettings() async {
    final ctrl = TextEditingController(text: _wsUrl);
    final newUrl = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: _panel,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.of(ctx).viewInsets.bottom),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('백엔드 WebSocket', style: TextStyle(color: _muted, fontSize: 11, letterSpacing: 1.2)),
            const SizedBox(height: 12),
            TextField(
              controller: ctrl,
              autofocus: true,
              style: const TextStyle(color: _fg, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'wss://<ngrok>.ngrok-free.dev',
                hintStyle: const TextStyle(color: _muted),
                filled: true, fillColor: const Color(0x10FFFFFF),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              '망 무관 접속: ngrok 터널\nPC에서 한 번 실행:\nngrok http 8765\n\n같은 Wi-Fi: ws://<PC LAN IP>:8765\nUSB: ws://localhost:8765 (adb reverse 후)',
              style: TextStyle(color: _muted2, fontSize: 11, height: 1.5),
            ),
            const SizedBox(height: 14),
            Row(children: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, '__disconnect__'),
                child: const Text('해제', style: TextStyle(color: _muted)),
              ),
              const Spacer(),
              ElevatedButton(
                onPressed: () => Navigator.pop(ctx, ctrl.text.trim()),
                style: ElevatedButton.styleFrom(backgroundColor: _accent, foregroundColor: const Color(0xFF04060A)),
                child: const Text('연결'),
              ),
            ]),
          ],
        ),
      ),
    );
    if (newUrl == '__disconnect__') {
      _bev.disconnect();
    } else if (newUrl != null && newUrl.isNotEmpty) {
      setState(() => _wsUrl = newUrl);
      _bev.connect(newUrl);
    }
  }

  @override
  Widget build(BuildContext context) {
    final opt = _options[_selected];
    final scale = _a11y ? 1.18 : 1.0;
    return Scaffold(
      floatingActionButton: _wsState == SocketState.connected
          ? FloatingActionButton.extended(
              backgroundColor: const Color(0xFFEF4444),
              foregroundColor: Colors.white,
              icon: const Text('🚨', style: TextStyle(fontSize: 18)),
              label: const Text('신고', style: TextStyle(fontWeight: FontWeight.w700)),
              onPressed: _showReportDialog,
            )
          : null,
      body: SafeArea(
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 110),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _Header(
                      wsState: _wsState,
                      payload: _livePayload,
                      impact: _impact,
                      telemetrySent: _telemetrySent,
                      onSettings: _showSettings),
                  const SizedBox(height: 10),
                  _ModeToggle(
                    mode: _mode,
                    onChanged: (m) => setState(() {
                      _mode = m;
                      _rebuild();
                    }),
                  ),
                  const SizedBox(height: 10),
                  _ContextBar(
                    station: _ctxName,
                    meta: _ctxLine,
                    time: _liveClock(),
                    scale: scale,
                    gpsKm: _stationDistKm,
                    onTapStation: _showStationPicker,
                  ),
                  if (_population != null && _population!.error == null &&
                      _population!.ppltnMid != null) ...[
                    const SizedBox(height: 4),
                    _PopulationStrip(p: _population!),
                  ],
                  if (_citydata != null && _citydata!.error == null) ...[
                    const SizedBox(height: 8),
                    _CitydataChips(c: _citydata!),
                    if (_citydata!.rainFirstDt != null) ...[
                      const SizedBox(height: 8),
                      _RainBanner(c: _citydata!),
                    ],
                    if (_citydata!.events.isNotEmpty ||
                        _citydata!.alerts.isNotEmpty ||
                        _citydata!.accidents.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      _SafetyBanner(c: _citydata!),
                    ],
                  ],
                  const SizedBox(height: 14),
                  _DecisionCard(
                      opt: opt,
                      mode: _mode,
                      hour: _hour,
                      scale: scale,
                      options: _options,
                      live: _livePayload),
                  const SizedBox(height: 14),
                  _ApproachCard(opt: opt, mode: _mode, scale: scale),
                  const SizedBox(height: 10),
                  _EtaCard(
                      seconds: opt.etaSeconds,
                      scale: scale,
                      live: _firstArrivalSeconds() != null && _arrivals?.simulated != true,
                      simulated: _arrivals?.simulated == true && _firstArrivalSeconds() != null),
                  const SizedBox(height: 14),
                  _MiniBevPanel(opt: opt, mode: _mode, livePersonCount: _livePayload?.personCount),
                  const SizedBox(height: 14),
                  _CompareCard(
                      options: _options,
                      selected: _selected,
                      mode: _mode,
                      scale: scale),
                  const SizedBox(height: 14),
                  if (_events != null && _events!.events.isNotEmpty) ...[
                    _EventsCard(ev: _events!),
                    const SizedBox(height: 14),
                  ],
                  if (opt.occ >= 0.92) const _AlertBanner(),
                  const SizedBox(height: 12),
                  _A11yToggle(
                      value: _a11y, onChanged: (v) => setState(() => _a11y = v)),
                  const SizedBox(height: 10),
                  _DemoTimeSlider(
                    hour: _hour,
                    onChanged: (v) => setState(() {
                      _hour = v.toInt();
                      _rebuild();
                    }),
                  ),
                ],
              ),
            ),
            // 하단 floating CTA
            Positioned(
              left: 0, right: 0, bottom: 0,
              child: IgnorePointer(
                ignoring: false,
                child: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter, end: Alignment.bottomCenter,
                      colors: [Color(0x0004060A), Color(0xCC04060A), Color(0xFF04060A)],
                    ),
                  ),
                  padding: const EdgeInsets.fromLTRB(16, 18, 16, 14),
                  child: _CTABar(
                    opt: opt,
                    mode: _mode,
                    onTap: () {
                      // 사회적 임팩트 로깅 — 권장 칸 탑승 시 절감률 추정.
                      final selOcc = opt.occ;
                      final allOcc = _options.map((o) => o.occ).toList();
                      if (allOcc.isNotEmpty) {
                        final avg =
                            allOcc.reduce((a, b) => a + b) / allOcc.length;
                        final saved = ((avg - selOcc) * 100).round();
                        if (saved > 0 && _wsState == SocketState.connected) {
                          _bev.logImpact(
                            station: _stationName,
                            car: opt.label,
                            savedPct: saved,
                          );
                        }
                      }
                    },
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============== Widgets ==============
class _Header extends StatelessWidget {
  final SocketState wsState;
  final BevPayload? payload;
  final ImpactSummary? impact;
  final int telemetrySent;
  final VoidCallback onSettings;
  const _Header({
    required this.wsState,
    required this.payload,
    required this.impact,
    required this.telemetrySent,
    required this.onSettings,
  });

  Color get _ledColor {
    switch (wsState) {
      case SocketState.connected: return _accent;
      case SocketState.connecting: return _warn;
      case SocketState.error: return _crit;
      default: return _muted;
    }
  }

  String get _liveLabel {
    if (wsState == SocketState.connected) {
      if (payload != null) {
        return 'LIVE · ${payload!.fps.toStringAsFixed(1)} fps · ${payload!.tracks.length} 트랙';
      }
      return 'LIVE';
    }
    if (wsState == SocketState.connecting) return '연결 중';
    if (wsState == SocketState.error) return '연결 실패';
    return '오프라인';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 6, height: 6,
            decoration: BoxDecoration(
              color: _ledColor, shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: _ledColor.withOpacity(0.55), blurRadius: 10, spreadRadius: 1),
              ],
            ),
          ),
          const SizedBox(width: 10),
          const Text('MetroEyes',
              style: TextStyle(color: _fg, fontSize: 14, fontWeight: FontWeight.w600)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(_liveLabel,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: wsState == SocketState.connected ? _accent : _muted,
                fontSize: 10, letterSpacing: 1.2,
                fontFeatures: const [FontFeature.tabularFigures()],
              )),
          ),
          if (telemetrySent > 0 && wsState == SocketState.connected) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0x14F0B46A),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: _warn.withOpacity(0.3)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.sensors_rounded, color: _warn, size: 11),
                  const SizedBox(width: 3),
                  Text(
                    '$telemetrySent',
                    style: const TextStyle(
                        color: _warn,
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                        fontFeatures: [FontFeature.tabularFigures()]),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 5),
          ],
          if (impact != null && impact!.totalCount > 0) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: _accentSoft,
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: _accent.withOpacity(0.25)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.eco_rounded, color: _accent, size: 11),
                  const SizedBox(width: 4),
                  Text(
                    '${impact!.totalCount}회 · 평균 -${impact!.avgSavedPct.round()}%',
                    style: const TextStyle(
                        color: _accent,
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                        fontFeatures: [FontFeature.tabularFigures()]),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 6),
          ],
          IconButton(
            onPressed: onSettings,
            icon: const Icon(Icons.tune_rounded, color: _muted, size: 20),
            tooltip: '백엔드 연결 설정',
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
          ),
        ],
      ),
    );
  }
}

class _ModeToggle extends StatelessWidget {
  final VehicleMode mode;
  final ValueChanged<VehicleMode> onChanged;
  const _ModeToggle({required this.mode, required this.onChanged});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _line, width: 1),
      ),
      child: Row(children: [
        for (final m in VehicleMode.values)
          Expanded(
            child: GestureDetector(
              onTap: () => onChanged(m),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: m == mode ? _accentSoft : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  border: m == mode
                      ? Border.all(color: _accent.withOpacity(0.25))
                      : null,
                ),
                child: Center(
                  child: Text(
                    m == VehicleMode.subway ? '지하철' : '버스',
                    style: TextStyle(
                      color: m == mode ? _accent : _muted,
                      fontSize: 13, fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ),
          ),
      ]),
    );
  }
}

class _ContextBar extends StatelessWidget {
  final String station, meta, time;
  final double scale;
  final double? gpsKm;
  final VoidCallback? onTapStation;
  const _ContextBar(
      {required this.station,
      required this.meta,
      required this.time,
      required this.scale,
      this.gpsKm,
      this.onTapStation});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 10, 4, 18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          // station + GPS km — 탭 시 station picker
          GestureDetector(
            onTap: onTapStation,
            behavior: HitTestBehavior.opaque,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(station,
                    style: TextStyle(
                        color: _fg,
                        fontSize: 18 * scale,
                        fontWeight: FontWeight.w500,
                        letterSpacing: -0.3)),
                const SizedBox(width: 4),
                Icon(Icons.expand_more_rounded,
                    color: _muted, size: 14 * scale),
                if (gpsKm != null) ...[
                  const SizedBox(width: 6),
                  Icon(Icons.my_location_rounded,
                      color: _accent, size: 11 * scale),
                  const SizedBox(width: 3),
                  Text(
                    gpsKm! < 1.0
                        ? '${(gpsKm! * 1000).round()}m'
                        : '${gpsKm!.toStringAsFixed(1)}km',
                    style: TextStyle(
                        color: _accent,
                        fontSize: 11 * scale,
                        fontFeatures: const [FontFeature.tabularFigures()]),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 6),
          Expanded(
              child: Text(meta,
                  style: TextStyle(color: _muted, fontSize: 13 * scale))),
          Text(time,
              style: TextStyle(
                  color: _muted,
                  fontSize: 13 * scale,
                  fontFeatures: const [FontFeature.tabularFigures()])),
        ],
      ),
    );
  }
}

class _PopulationStrip extends StatelessWidget {
  final PopulationResponse p;
  const _PopulationStrip({required this.p});

  Color _lvlColor(String? lvl) {
    switch (lvl) {
      case '붐빔': return _crit;
      case '약간 붐빔': return _warn;
      case '보통': return _accent;
      case '여유': return _accent;
      default: return _muted;
    }
  }

  String _formatN(int n) {
    if (n >= 10000) {
      final k = (n / 1000).round();
      return '${(k / 10).toStringAsFixed(1)}만';
    }
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return '$n';
  }

  @override
  Widget build(BuildContext context) {
    final mid = p.ppltnMid!;
    final lvl = p.congestLvl ?? '?';
    final lvlColor = _lvlColor(lvl);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(Icons.groups_2_rounded, color: lvlColor, size: 14),
          const SizedBox(width: 8),
          Text(p.areaNm ?? p.poi,
              style: const TextStyle(color: _muted, fontSize: 11)),
          const SizedBox(width: 8),
          Text('${_formatN(mid)}명',
              style: const TextStyle(
                  color: _fg,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  fontFeatures: [FontFeature.tabularFigures()])),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
                color: lvlColor.withOpacity(0.15),
                borderRadius: BorderRadius.circular(4)),
            child: Text(lvl,
                style: TextStyle(
                    color: lvlColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w500)),
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
                color: _accentSoft, borderRadius: BorderRadius.circular(4)),
            child: const Text('서울 도시데이터',
                style: TextStyle(
                    color: _accent,
                    fontSize: 9,
                    letterSpacing: 0.8,
                    fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}

class _DecisionCard extends StatelessWidget {
  final Option opt;
  final VehicleMode mode;
  final int hour;
  final double scale;
  final List<Option> options;
  final BevPayload? live;
  const _DecisionCard(
      {required this.opt,
      required this.mode,
      required this.hour,
      required this.scale,
      required this.options,
      required this.live});
  @override
  Widget build(BuildContext context) {
    final pct = (opt.occ * 100).round();
    final isLive = live != null && live!.personCount > 0;
    // 편성 평균: 라이브가 있으면 칸별 평균, 없으면 시뮬 곡선.
    final avg = isLive
        ? (options.map((o) => o.occ).reduce((a, b) => a + b) /
                options.length *
                100)
            .round()
        : (trainOccupancy(hour, 'hub') * 100).round();
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: const Alignment(-0.5, -1),
          end: const Alignment(0.7, 1),
          colors: [_accent.withOpacity(0.08), _accent.withOpacity(0.02)],
        ),
        border: Border.all(color: _accent.withOpacity(0.28)),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            mode == VehicleMode.subway ? '권장 탑승 칸' : '권장 탑승 차량',
            style: const TextStyle(
                color: _accent,
                fontSize: 11,
                fontWeight: FontWeight.w500,
                letterSpacing: 1.4),
          ),
          const SizedBox(height: 10),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(opt.label,
                  style: TextStyle(
                      color: _fg,
                      fontSize: 22 * scale,
                      fontWeight: FontWeight.w500)),
              const SizedBox(width: 12),
              Text('$pct',
                  style: TextStyle(
                      color: _fg,
                      fontSize: 56 * scale,
                      fontWeight: FontWeight.w200,
                      letterSpacing: -2,
                      fontFeatures: const [FontFeature.tabularFigures()])),
              const SizedBox(width: 4),
              Text('%',
                  style: TextStyle(
                      color: _muted,
                      fontSize: 22 * scale,
                      fontWeight: FontWeight.w300)),
            ],
          ),
          const SizedBox(height: 10),
          RichText(
            text: TextSpan(
              style: TextStyle(
                  color: _muted2, fontSize: 13 * scale, height: 1.5),
              children: [
                TextSpan(text: isLive ? '실측 평균 ' : '편성 평균 '),
                TextSpan(
                    text: '$avg%',
                    style: const TextStyle(
                        color: _accent, fontWeight: FontWeight.w500)),
                TextSpan(
                    text: isLive
                        ? '보다 한산. 라이브 카메라 ${live!.personCount}명 검출.'
                        : '보다 한산. 환승 허브 시간대.'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ApproachCard extends StatelessWidget {
  final Option opt;
  final VehicleMode mode;
  final double scale;
  const _ApproachCard(
      {required this.opt, required this.mode, required this.scale});
  @override
  Widget build(BuildContext context) {
    final isSubway = mode == VehicleMode.subway;
    final headText = isSubway ? '승강장 마커로 이동' : '도착 대기';
    final detail = isSubway
        ? '<b>마커 ${opt.idx + 1}번</b>까지 약 ${20 + opt.idx * 12}m · 도보 ${math.max(15, 20 + opt.idx * 6)}초'
        : '<b>${opt.idx + 1}순위</b> 차량 · 약 <b>${(opt.etaSeconds / 60).round()}분 후</b>';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 38, height: 38, alignment: Alignment.center,
            decoration: BoxDecoration(
              color: _accentSoft, borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.directions_walk, color: _accent, size: 20 * scale),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(headText,
                    style: const TextStyle(
                        color: _muted, fontSize: 11, letterSpacing: 1.2)),
                const SizedBox(height: 4),
                _RichBoldText(
                    text: detail,
                    baseStyle: TextStyle(color: _fg, fontSize: 14 * scale)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RichBoldText extends StatelessWidget {
  final String text;
  final TextStyle baseStyle;
  const _RichBoldText({required this.text, required this.baseStyle});
  @override
  Widget build(BuildContext context) {
    final spans = <TextSpan>[];
    final pattern = RegExp(r'<b>(.+?)</b>');
    var lastEnd = 0;
    for (final m in pattern.allMatches(text)) {
      if (m.start > lastEnd) {
        spans.add(TextSpan(text: text.substring(lastEnd, m.start)));
      }
      spans.add(TextSpan(
          text: m.group(1),
          style: const TextStyle(color: _fg, fontWeight: FontWeight.w500)));
      lastEnd = m.end;
    }
    if (lastEnd < text.length) {
      spans.add(TextSpan(text: text.substring(lastEnd)));
    }
    return RichText(text: TextSpan(style: baseStyle, children: spans));
  }
}

class _EtaCard extends StatelessWidget {
  final int seconds;
  final double scale;
  final bool live;
  final bool simulated;
  const _EtaCard({required this.seconds, required this.scale,
      this.live = false, this.simulated = false});
  @override
  Widget build(BuildContext context) {
    final m = seconds ~/ 60, s = seconds % 60;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          const Text('도착',
              style: TextStyle(
                  color: _muted, fontSize: 11, letterSpacing: 1.2)),
          if (live || simulated) ...[
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                  color: simulated
                      ? const Color(0x1AF0B46A)
                      : _accentSoft,
                  borderRadius: BorderRadius.circular(4)),
              child: Text(simulated ? 'SIM' : 'LIVE',
                  style: TextStyle(
                      color: simulated ? _warn : _accent,
                      fontSize: 9,
                      letterSpacing: 1.1,
                      fontWeight: FontWeight.w600)),
            ),
          ],
          const Spacer(),
          Text('$m',
              style: TextStyle(
                  color: _fg,
                  fontSize: 28 * scale,
                  fontWeight: FontWeight.w300,
                  fontFeatures: const [FontFeature.tabularFigures()])),
          Text('분 ', style: TextStyle(color: _muted, fontSize: 14 * scale)),
          if (s > 0) ...[
            Text('$s',
                style: TextStyle(
                    color: _fg,
                    fontSize: 28 * scale,
                    fontWeight: FontWeight.w300)),
            Text('초', style: TextStyle(color: _muted, fontSize: 14 * scale)),
          ],
        ],
      ),
    );
  }
}

class _MiniBevPanel extends StatelessWidget {
  final Option opt;
  final VehicleMode mode;
  final int? livePersonCount;
  const _MiniBevPanel({required this.opt, required this.mode, this.livePersonCount});
  @override
  Widget build(BuildContext context) {
    final isLive = livePersonCount != null;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(isLive ? '실시간 BEV · 백엔드 연결' : '실시간 BEV · ${opt.label}',
                  style: const TextStyle(color: _muted, fontSize: 11, letterSpacing: 1.2)),
              const Spacer(),
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                    color: isLive ? _accent : _muted, shape: BoxShape.circle),
              ),
              const SizedBox(width: 5),
              Text(isLive ? 'LIVE 백엔드' : 'SIM',
                  style: TextStyle(
                      color: isLive ? _accent : _muted,
                      fontSize: 11,
                      fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 8),
          AspectRatio(
            aspectRatio: mode == VehicleMode.subway ? 5 / 1.05 : 5 / 1.5,
            child: CustomPaint(painter: BevMiniPainter(occ: opt.occ, mode: mode)),
          ),
          if (isLive) Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              '카메라 검출 $livePersonCount명 → 칸별 분포 라이브 적용',
              style: const TextStyle(color: _accent, fontSize: 11, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }

}

class BevMiniPainter extends CustomPainter {
  final double occ;
  final VehicleMode mode;
  BevMiniPainter({required this.occ, required this.mode});

  @override
  void paint(Canvas canvas, Size size) {
    const pad = 8.0;
    final w = size.width - pad * 2, h = size.height - pad * 2;
    final rect = Rect.fromLTWH(pad, pad, w, h);
    final rr = RRect.fromRectAndRadius(rect, const Radius.circular(14));
    canvas.drawRRect(rr, Paint()..color = const Color(0xFF0C1018));
    canvas.drawRRect(
        rr,
        Paint()
          ..color = _accent.withOpacity(0.15)
          ..style = PaintingStyle.stroke);

    // 좌석
    final seatPaint = Paint()..color = Colors.white.withOpacity(0.05);
    final seatBlocks = mode == VehicleMode.subway ? 6 : 4;
    final seatsPer = mode == VehicleMode.subway ? 7 : 4;
    const gap = 6.0;
    final bw = (w - (seatBlocks + 1) * gap) / seatBlocks;
    final sh = h * 0.18;
    for (final side in [0, 1]) {
      final yc = side == 0 ? pad + 6 + sh / 2 : pad + h - sh - 6 + sh / 2;
      for (var b = 0; b < seatBlocks; b++) {
        final bx = pad + gap + b * (bw + gap);
        for (var s = 0; s < seatsPer; s++) {
          final sx = bx + (s + 0.5) * (bw / seatsPer);
          canvas.drawRRect(
            RRect.fromRectAndRadius(
                Rect.fromLTWH(sx - 4, yc - 4, 8, 8), const Radius.circular(2)),
            seatPaint,
          );
        }
      }
    }
    // 출입문
    final doorXs =
        mode == VehicleMode.subway ? [0.18, 0.42, 0.58, 0.82] : [0.18, 0.55];
    final doorPaint = Paint()..color = _accent.withOpacity(0.55);
    for (var i = 0; i < doorXs.length; i++) {
      final x = pad + doorXs[i] * w;
      canvas.drawRect(Rect.fromLTWH(x - 16, pad - 1, 32, 2), doorPaint);
      if (mode == VehicleMode.subway) {
        canvas.drawRect(
            Rect.fromLTWH(x - 16, pad + h - 1, 32, 2), doorPaint);
      } else {
        final color = i == 0 ? _accent : const Color(0xFFF0AA82);
        final p = Paint()..color = color.withOpacity(0.55);
        canvas.drawRect(Rect.fromLTWH(x - 16, pad + h - 1, 32, 2), p);
      }
    }
    // 사람 점들
    final cnt = (occ * (mode == VehicleMode.subway ? 160 : 50)).round();
    final rng = math.Random(42);
    final personPaint = Paint()..color = _fg.withOpacity(0.85);
    for (var i = 0; i < cnt; i++) {
      final inSeat = i < seatBlocks * seatsPer * 2;
      double x, y;
      if (inSeat) {
        final side = i % 2;
        final idx = i ~/ 2;
        final blk = idx ~/ seatsPer;
        final s = idx % seatsPer;
        final bx = pad + gap + blk * (bw + gap);
        x = bx + (s + 0.5) * (bw / seatsPer);
        y = side == 0 ? pad + 6 + sh / 2 : pad + h - sh - 6 + sh / 2;
      } else {
        x = pad + 8 + rng.nextDouble() * (w - 16);
        y = pad + sh + 4 + rng.nextDouble() * (h - sh * 2 - 8);
      }
      canvas.drawCircle(Offset(x, y), 1.6, personPaint);
    }
    // 점유율 라벨
    final tp = TextPainter(
      text: TextSpan(
          text: '${(occ * 100).round()}% · $cnt명',
          style: const TextStyle(
              color: _fg, fontSize: 10, fontWeight: FontWeight.w500)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, Offset(size.width - tp.width - 12, pad + 4));
  }

  @override
  bool shouldRepaint(covariant BevMiniPainter oldDelegate) =>
      oldDelegate.occ != occ || oldDelegate.mode != mode;
}

class _CompareCard extends StatelessWidget {
  final List<Option> options;
  final int selected;
  final VehicleMode mode;
  final double scale;
  const _CompareCard(
      {required this.options,
      required this.selected,
      required this.mode,
      required this.scale});
  @override
  Widget build(BuildContext context) {
    final selOcc = options[selected].occ;
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 10),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('다른 선택지',
              style: TextStyle(
                  color: _muted, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 8),
          for (var i = 0; i < options.length; i++)
            if (i != selected)
              _CompareRow(
                  opt: options[i],
                  pickedOcc: selOcc,
                  mode: mode,
                  scale: scale),
        ],
      ),
    );
  }
}

class _CompareRow extends StatelessWidget {
  final Option opt;
  final double pickedOcc;
  final VehicleMode mode;
  final double scale;
  const _CompareRow(
      {required this.opt,
      required this.pickedOcc,
      required this.mode,
      required this.scale});
  @override
  Widget build(BuildContext context) {
    final pct = (opt.occ * 100).round();
    final cls = opt.occ > 0.85 ? _crit : opt.occ > 0.65 ? _warn : _fg;
    final verdict = opt.occ < pickedOcc
        ? '더 한산'
        : opt.occ > 0.85 ? '비추' : '비슷';
    final verdictColor = opt.occ < pickedOcc
        ? _accent
        : opt.occ > 0.85 ? _crit : _muted;
    final whenText = mode == VehicleMode.subway
        ? (opt.idx == 0 ? '지금' : '${opt.idx}회 뒤')
        : '${(opt.etaSeconds / 60).round()}분 후';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(
              width: 60,
              child: Text(whenText,
                  style: TextStyle(color: _muted, fontSize: 13 * scale))),
          const SizedBox(width: 8),
          Expanded(
            child: Container(
              height: 4,
              decoration: BoxDecoration(
                color: const Color(0x10FFFFFF),
                borderRadius: BorderRadius.circular(999),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: math.min(1.0, opt.occ),
                child: Container(
                  decoration: BoxDecoration(
                      color: cls, borderRadius: BorderRadius.circular(999)),
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
              width: 50,
              child: Text('$pct%',
                  textAlign: TextAlign.right,
                  style: TextStyle(color: _fg, fontSize: 13 * scale))),
          const SizedBox(width: 6),
          SizedBox(
              width: 56,
              child: Text(verdict,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                      color: verdictColor,
                      fontSize: 11 * scale,
                      fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }
}

class _AlertBanner extends StatelessWidget {
  const _AlertBanner();
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: _crit.withOpacity(0.10),
        border: Border.all(color: _crit.withOpacity(0.35)),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Row(
        children: [
          Icon(Icons.warning_rounded, color: _crit, size: 18),
          SizedBox(width: 10),
          Expanded(
              child: Text('임계 밀집 — 다음 차 +3분 대기 권고',
                  style: TextStyle(color: _crit, fontSize: 13))),
        ],
      ),
    );
  }
}

class _A11yToggle extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;
  const _A11yToggle({required this.value, required this.onChanged});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(children: [
        const Expanded(
          child: Text(
            '약자 모드 (큰 글씨 · 휠체어/유아차 동선)',
            style: TextStyle(color: _muted2, fontSize: 13),
          ),
        ),
        Switch.adaptive(
          value: value,
          onChanged: onChanged,
          activeColor: _accent,
          inactiveTrackColor: const Color(0xFF1A2230),
        ),
      ]),
    );
  }
}

class _DemoTimeSlider extends StatelessWidget {
  final int hour;
  final ValueChanged<double> onChanged;
  const _DemoTimeSlider({required this.hour, required this.onChanged});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(children: [
        const Text('데모 시각',
            style:
                TextStyle(color: _muted, fontSize: 11, letterSpacing: 1.2)),
        Expanded(
          child: SliderTheme(
            data: SliderThemeData(
              trackHeight: 2,
              thumbShape:
                  const RoundSliderThumbShape(enabledThumbRadius: 7),
              overlayShape:
                  const RoundSliderOverlayShape(overlayRadius: 16),
              activeTrackColor: _fg,
              inactiveTrackColor: _line2,
              thumbColor: _fg,
              overlayColor: _fg.withOpacity(0.10),
            ),
            child: Slider(
              value: hour.toDouble(),
              min: 5,
              max: 23,
              divisions: 18,
              onChanged: onChanged,
            ),
          ),
        ),
        SizedBox(
          width: 36,
          child: Text(
            '$hour시',
            textAlign: TextAlign.right,
            style: const TextStyle(
                color: _fg,
                fontSize: 13,
                fontFeatures: [FontFeature.tabularFigures()]),
          ),
        ),
      ]),
    );
  }
}

class _CTABar extends StatelessWidget {
  final Option opt;
  final VehicleMode mode;
  final VoidCallback? onTap;
  const _CTABar({required this.opt, required this.mode, this.onTap});
  @override
  Widget build(BuildContext context) {
    return Container(
      color: _bg,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 22),
      child: GestureDetector(
        onTap: () {
          onTap?.call();
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('${opt.label} 탑승 — 임팩트 기록됨',
                style: const TextStyle(color: Color(0xFF04060A))),
            backgroundColor: _accent,
            duration: const Duration(seconds: 2),
          ));
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            color: _accent,
            borderRadius: BorderRadius.circular(999),
            boxShadow: [
              BoxShadow(
                  color: _accent.withOpacity(0.25),
                  blurRadius: 24,
                  offset: const Offset(0, 8)),
            ],
          ),
          child: const Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '탑승하기',
                  style: TextStyle(
                    color: Color(0xFF04060A),
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    letterSpacing: -0.2,
                  ),
                ),
                SizedBox(width: 6),
                Icon(Icons.arrow_forward_rounded, color: Color(0xFF04060A), size: 18),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ============== 도시데이터 위젯 ==============

class _CitydataChips extends StatelessWidget {
  final CitydataResponse c;
  const _CitydataChips({required this.c});

  Color _airColor(String? idx) {
    switch (idx) {
      case '좋음': return _accent;
      case '보통': return _muted2;
      case '나쁨': return _warn;
      case '매우나쁨': return _crit;
      default: return _muted;
    }
  }

  Color _roadColor(String? idx) {
    switch (idx) {
      case '원활': return _accent;
      case '서행': return _warn;
      case '정체': return _crit;
      default: return _muted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final chips = <Widget>[];
    // 날씨
    if (c.temp != null) {
      final t = c.temp!.toStringAsFixed(0);
      final st = c.sensibleTemp?.toStringAsFixed(0);
      chips.add(_chip(
        Icons.thermostat_rounded,
        st != null && st != t ? '$t° (체감 $st°)' : '$t°',
        _accent,
      ));
    }
    // 공기질 (PM2.5)
    if (c.pm25 != null) {
      chips.add(_chip(
        Icons.air_rounded,
        'PM2.5 ${c.pm25} · ${c.pm25Idx ?? "-"}',
        _airColor(c.pm25Idx ?? c.airIdx),
      ));
    }
    // UV
    if (c.uvLvl != null && c.uvLvl! > 0) {
      chips.add(_chip(
        Icons.wb_sunny_outlined,
        'UV ${c.uvLvl}',
        c.uvLvl! >= 6 ? _warn : _muted2,
      ));
    }
    // 도로
    if (c.roadAvgSpeed != null) {
      chips.add(_chip(
        Icons.alt_route_rounded,
        '${c.roadAvgSpeed!.toStringAsFixed(0)}km/h · ${c.roadAvgIdx ?? "-"}',
        _roadColor(c.roadAvgIdx),
      ));
    }
    // 따릉이
    if (c.sbikeSharedTotal > 0) {
      chips.add(_chip(
        Icons.pedal_bike_rounded,
        '따릉이 ${c.sbikeSharedTotal}',
        _accent,
      ));
    }
    // 주차
    if (c.parkingAvailTotal > 0) {
      chips.add(_chip(
        Icons.local_parking_rounded,
        '주차 ${c.parkingAvailTotal}',
        _muted2,
      ));
    }
    if (chips.isEmpty) return const SizedBox.shrink();
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (var i = 0; i < chips.length; i++) ...[
            chips[i],
            if (i < chips.length - 1) const SizedBox(width: 6),
          ],
        ],
      ),
    );
  }

  Widget _chip(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 12),
          const SizedBox(width: 5),
          Text(text,
              style: TextStyle(
                  color: _fg,
                  fontSize: 11,
                  fontFeatures: const [FontFeature.tabularFigures()])),
        ],
      ),
    );
  }
}

class _RainBanner extends StatelessWidget {
  final CitydataResponse c;
  const _RainBanner({required this.c});

  String _typeText(String? t) {
    switch (t) {
      case '비': return '비';
      case '눈': return '눈';
      case '진눈깨비': return '진눈깨비';
      case '소나기': return '소나기';
      default: return t ?? '강수';
    }
  }

  String _shortDt(String? dt) {
    if (dt == null || dt.length < 16) return dt ?? '';
    // YYYY-MM-DD HH:MM → HH:MM
    return dt.substring(11, 16);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0x1A7DD3D3),
        border: Border.all(color: _accent.withOpacity(0.30)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          const Icon(Icons.umbrella_rounded, color: _accent, size: 14),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '${_shortDt(c.rainFirstDt)} ${_typeText(c.rainFirstType)} 시작 — 우산 챙기세요',
              style: const TextStyle(
                  color: _accent,
                  fontSize: 12,
                  fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}

class _SafetyBanner extends StatelessWidget {
  final CitydataResponse c;
  const _SafetyBanner({required this.c});

  @override
  Widget build(BuildContext context) {
    final n = c.events.length + c.alerts.length + c.accidents.length;
    final isCrit = c.alerts.isNotEmpty || c.accidents.isNotEmpty;
    final color = isCrit ? _crit : _warn;
    final label = isCrit
        ? '안전 알림 · 사고/특보 ${c.alerts.length + c.accidents.length}건'
        : '주변 행사 영향 · ${c.events.length}건';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        border: Border.all(color: color.withOpacity(0.35)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(isCrit ? Icons.warning_rounded : Icons.event_note_rounded,
              color: color, size: 14),
          const SizedBox(width: 8),
          Expanded(
            child: Text(label,
                style: TextStyle(
                    color: color, fontSize: 12, fontWeight: FontWeight.w500)),
          ),
          Text('총 $n',
              style: TextStyle(color: color.withOpacity(0.7), fontSize: 11)),
        ],
      ),
    );
  }
}

class _EventsCard extends StatelessWidget {
  final EventsResponse ev;
  const _EventsCard({required this.ev});

  String _formatN(int n) {
    if (n >= 10000) return '${(n / 10000).toStringAsFixed(1)}만';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return '$n';
  }

  @override
  Widget build(BuildContext context) {
    final rows = ev.events.take(3).toList();
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.celebration_rounded, color: _warn, size: 14),
              const SizedBox(width: 6),
              const Text('주변 행사 / 인구 신호',
                  style: TextStyle(
                      color: _muted, fontSize: 11, letterSpacing: 1.2)),
              const Spacer(),
              if (ev.totalCapacity > 0)
                Text('정원 ${_formatN(ev.totalCapacity)}',
                    style: const TextStyle(color: _warn, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 8),
          for (final r in rows)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      r.name ?? '행사',
                      style: const TextStyle(color: _fg, fontSize: 13),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (r.vMax != null)
                    Text('${_formatN(r.vMax!)}명',
                        style: const TextStyle(color: _muted2, fontSize: 11)),
                  if (r.distKm != null) ...[
                    const SizedBox(width: 8),
                    Text(
                      r.distKm! < 1.0
                          ? '${(r.distKm! * 1000).round()}m'
                          : '${r.distKm!.toStringAsFixed(1)}km',
                      style: const TextStyle(color: _accent, fontSize: 11),
                    ),
                  ],
                ],
              ),
            ),
          if (ev.events.length > 3)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('외 ${ev.events.length - 3}건',
                  style: const TextStyle(color: _muted, fontSize: 11)),
            ),
        ],
      ),
    );
  }
}
