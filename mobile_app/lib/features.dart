import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:maplibre_gl/maplibre_gl.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:vibration/vibration.dart';
import 'i18n.dart';
import 'bev_socket.dart';

// ── 디자인 토큰 (main.dart와 동일)
const _panel = Color(0xFF0A0D14);
const _line = Color(0x12FFFFFF);
const _fg = Color(0xFFE8EDF5);
const _muted = Color(0xFF6B768A);
const _muted2 = Color(0xFF8E98AC);
const _accent = Color(0xFF7DD3D3);
const _accentSoft = Color(0x1A7DD3D3);
const _warn = Color(0xFFF0B46A);
const _crit = Color(0xFFFF5E57);

// ── 유틸
Widget _cardWrap({required Widget child, Color? borderColor}) => Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: _panel,
        border: Border.all(color: borderColor ?? _line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: child,
    );

// ══════════════════════════════════════════════════════
// 1. 도착지 STT 카드
// ══════════════════════════════════════════════════════
class DestCard extends StatefulWidget {
  final String currentStation;
  final bool wsConnected;
  final void Function(String?) onDestChanged;
  final String? dest;
  const DestCard({
    super.key,
    required this.currentStation,
    required this.wsConnected,
    required this.onDestChanged,
    this.dest,
  });
  @override
  State<DestCard> createState() => _DestCardState();
}

class _DestCardState extends State<DestCard> {
  final _speech = SpeechToText();
  bool _isListening = false;
  String _statusText = '';
  bool _sttAvailable = false;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    final ok = await _speech.initialize(
      onError: (_) => setState(() => _isListening = false),
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          setState(() => _isListening = false);
        }
      },
    );
    if (mounted) setState(() => _sttAvailable = ok);
  }

  Future<void> _listen() async {
    if (!_sttAvailable) return;
    if (_isListening) {
      await _speech.stop();
      setState(() => _isListening = false);
      return;
    }
    setState(() {
      _isListening = true;
      _statusText = t('stt_listen');
    });
    final locale = langLocales[langNotifier.value] ?? 'ko_KR';
    await _speech.listen(
      localeId: locale,
      onResult: (result) {
        if (result.finalResult && result.recognizedWords.isNotEmpty) {
          setState(() {
            _statusText = result.recognizedWords;
            _isListening = false;
          });
          widget.onDestChanged(result.recognizedWords);
        }
      },
      listenFor: const Duration(seconds: 10),
      pauseFor: const Duration(seconds: 3),
    );
  }

  @override
  Widget build(BuildContext context) {
    final dest = widget.dest;
    return _cardWrap(
      borderColor: dest != null ? _accent.withValues(alpha: 0.35) : _line,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(t('set_dest'),
                  style: const TextStyle(
                      color: _muted, fontSize: 11, letterSpacing: 1.2)),
              const Spacer(),
              if (dest != null)
                GestureDetector(
                  onTap: () => widget.onDestChanged(null),
                  child: Text(t('dest_clear'),
                      style: const TextStyle(color: _crit, fontSize: 11)),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: dest != null
                    ? Row(
                        children: [
                          const Icon(Icons.location_on_rounded,
                              color: _accent, size: 14),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(dest,
                                style: const TextStyle(
                                    color: _accent,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500),
                                overflow: TextOverflow.ellipsis),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 7, vertical: 2),
                            decoration: BoxDecoration(
                              color: _accentSoft,
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(t('dest_active'),
                                style: const TextStyle(
                                    color: _accent, fontSize: 10)),
                          ),
                          const SizedBox(width: 6),
                          GestureDetector(
                            onTap: () async {
                              await triggerArrivalAlert();
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 7, vertical: 2),
                              decoration: BoxDecoration(
                                color: _warn.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(999),
                                border: Border.all(
                                    color:
                                        _warn.withValues(alpha: 0.35)),
                              ),
                              child: const Text('🔔 테스트',
                                  style: TextStyle(
                                      color: _warn, fontSize: 10)),
                            ),
                          ),
                        ],
                      )
                    : Text(
                        _isListening ? _statusText : t('stt_tap'),
                        style: TextStyle(
                            color: _isListening ? _warn : _muted2,
                            fontSize: 13),
                      ),
              ),
              const SizedBox(width: 10),
              GestureDetector(
                onTap: _listen,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: _isListening
                        ? _warn.withValues(alpha: 0.15)
                        : _accentSoft,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _isListening
                          ? _warn.withValues(alpha: 0.5)
                          : _accent.withValues(alpha: 0.3),
                    ),
                  ),
                  child: Icon(
                    _isListening ? Icons.stop_rounded : Icons.mic_rounded,
                    color: _isListening ? _warn : _accent,
                    size: 20,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _speech.cancel();
    super.dispose();
  }
}

// ══════════════════════════════════════════════════════
// 2. AI 채팅 카드
// ══════════════════════════════════════════════════════
class ChatCard extends StatefulWidget {
  final BevSocket bev;
  final bool wsConnected;
  final String station;
  final List<ChatMessage> history;
  final void Function(ChatMessage) onNewMessage;
  const ChatCard({
    super.key,
    required this.bev,
    required this.wsConnected,
    required this.station,
    required this.history,
    required this.onNewMessage,
  });
  @override
  State<ChatCard> createState() => _ChatCardState();
}

class _ChatCardState extends State<ChatCard> {
  final _ctrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _sending = false;
  bool _expanded = false;

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    if (!widget.wsConnected) {
      widget.onNewMessage(
          ChatMessage(text: t('chat_offline'), isUser: false));
      return;
    }
    final userMsg = ChatMessage(text: text, isUser: true);
    widget.onNewMessage(userMsg);
    widget.bev.sendChat(text, widget.station);
    _ctrl.clear();
    setState(() => _sending = true);
    Future.delayed(const Duration(seconds: 8),
        () => { if (mounted) setState(() => _sending = false) });
  }

  @override
  Widget build(BuildContext context) {
    return _cardWrap(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: () => setState(() => _expanded = !_expanded),
            child: Row(
              children: [
                Text(t('ask_llm'),
                    style: const TextStyle(
                        color: _muted, fontSize: 11, letterSpacing: 1.2)),
                const Spacer(),
                Icon(
                  _expanded
                      ? Icons.keyboard_arrow_up_rounded
                      : Icons.keyboard_arrow_down_rounded,
                  color: _muted,
                  size: 18,
                ),
              ],
            ),
          ),
          if (_expanded) ...[
            const SizedBox(height: 10),
            if (widget.history.isNotEmpty) ...[
              SizedBox(
                height: 180,
                child: ListView.builder(
                  controller: _scrollCtrl,
                  itemCount: widget.history.length +
                      (_sending ? 1 : 0),
                  itemBuilder: (ctx, i) {
                    if (_sending && i == widget.history.length) {
                      return _bubble(t('thinking'), false, typing: true);
                    }
                    final msg = widget.history[i];
                    return _bubble(msg.text, msg.isUser);
                  },
                ),
              ),
              const SizedBox(height: 8),
            ],
            // 빠른 질문 chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final q in [
                    '강남역까지 빠르게',
                    '지금 가장 한산한 차',
                    '휠체어로 갈 수 있어?',
                    '홍대까지 가는 법',
                  ])
                    Padding(
                      padding: const EdgeInsets.only(right: 6, bottom: 8),
                      child: GestureDetector(
                        onTap: () {
                          _ctrl.text = q;
                          _send();
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: _accentSoft,
                            borderRadius: BorderRadius.circular(999),
                            border: Border.all(
                                color: _accent.withValues(alpha: 0.25)),
                          ),
                          child: Text(q,
                              style: const TextStyle(
                                  color: _accent,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w500)),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    style: const TextStyle(color: _fg, fontSize: 13),
                    onSubmitted: (_) => _send(),
                    decoration: InputDecoration(
                      hintText: t('chat_hint'),
                      hintStyle: const TextStyle(color: _muted, fontSize: 13),
                      filled: true,
                      fillColor: const Color(0x10FFFFFF),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: _send,
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: _accentSoft,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                          color: _accent.withValues(alpha: 0.3)),
                    ),
                    child: const Icon(Icons.send_rounded,
                        color: _accent, size: 18),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _bubble(String text, bool isUser, {bool typing = false}) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        constraints: const BoxConstraints(maxWidth: 260),
        decoration: BoxDecoration(
          color: isUser
              ? _accent.withValues(alpha: 0.15)
              : _panel.withValues(alpha: 0.0),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: isUser
                  ? _accent.withValues(alpha: 0.3)
                  : _line),
        ),
        child: typing
            ? const _TypingDots()
            : Text(text,
                style: TextStyle(
                    color: isUser ? _accent : _fg, fontSize: 12)),
      ),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }
}

class _TypingDots extends StatefulWidget {
  const _TypingDots();
  @override
  State<_TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<_TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _anim;
  @override
  void initState() {
    super.initState();
    _anim = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final offset = ((_anim.value * 3) - i).clamp(0.0, 1.0);
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _muted.withValues(
                    alpha: 0.3 + 0.7 * math.sin(offset * math.pi).abs()),
              ),
            );
          }),
        );
      },
    );
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }
}

// ══════════════════════════════════════════════════════
// 3. 24시간 혼잡 예측 카드
// ══════════════════════════════════════════════════════
class ForecastCard extends StatelessWidget {
  final List<double> occupancies;
  final List<int> hours;
  const ForecastCard(
      {super.key, required this.occupancies, required this.hours});

  @override
  Widget build(BuildContext context) {
    return _cardWrap(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t('surge_forecast'),
              style: const TextStyle(
                  color: _muted, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              for (var i = 0; i < occupancies.length; i++) ...[
                Expanded(
                  child: Column(
                    children: [
                      Container(
                        height: 60,
                        alignment: Alignment.bottomCenter,
                        child: FractionallySizedBox(
                          heightFactor: occupancies[i].clamp(0.0, 1.0),
                          child: Container(
                            decoration: BoxDecoration(
                              color: _barColor(occupancies[i]),
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(4)),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${hours[i]}${t('hour_suffix')}',
                        style: const TextStyle(
                            color: _muted, fontSize: 9),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
                if (i < occupancies.length - 1) const SizedBox(width: 4),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Color _barColor(double occ) {
    if (occ > 0.85) return _crit;
    if (occ > 0.65) return _warn;
    return _accent;
  }
}

// ══════════════════════════════════════════════════════
// 4. 엘리베이터 상태 카드
// ══════════════════════════════════════════════════════
class ElevatorCard extends StatelessWidget {
  final String station;
  const ElevatorCard({super.key, required this.station});

  // 역명 해시 기반 결정적 mock (85% 정상)
  List<bool> _statuses() {
    final hash = station.codeUnits.fold(0, (a, b) => a + b);
    final day = DateTime.now().day;
    return List.generate(3, (i) => (hash + day + i * 7) % 7 != 0);
  }

  @override
  Widget build(BuildContext context) {
    final statuses = _statuses();
    return _cardWrap(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t('elevator'),
              style: const TextStyle(
                  color: _muted, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 10),
          Row(
            children: [
              for (var i = 0; i < statuses.length; i++) ...[
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    decoration: BoxDecoration(
                      color: statuses[i]
                          ? _accent.withValues(alpha: 0.08)
                          : _crit.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: statuses[i]
                            ? _accent.withValues(alpha: 0.25)
                            : _crit.withValues(alpha: 0.25),
                      ),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          Icons.elevator_rounded,
                          color: statuses[i] ? _accent : _crit,
                          size: 20,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${i + 1}번',
                          style: const TextStyle(
                              color: _muted, fontSize: 10),
                        ),
                        Text(
                          statuses[i] ? t('elev_ok') : t('elev_fail'),
                          style: TextStyle(
                            color: statuses[i] ? _accent : _crit,
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                if (i < statuses.length - 1) const SizedBox(width: 6),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

// ══════════════════════════════════════════════════════
// 5. OD·환승 보너스 + CO₂ 보상 칩
// ══════════════════════════════════════════════════════
class RewardChips extends StatelessWidget {
  final ODBonusResponse? odBonus;
  final TransferBonusResponse? transferBonus;
  final ImpactSummary? impact;
  const RewardChips({
    super.key,
    this.odBonus,
    this.transferBonus,
    this.impact,
  });

  @override
  Widget build(BuildContext context) {
    final chips = <Widget>[];
    if (odBonus != null) {
      chips.add(_chip(
        '${t('od_bonus')} ${odBonus!.label}',
        Icons.swap_horiz_rounded,
        _warn,
      ));
    }
    if (transferBonus != null && transferBonus!.active) {
      chips.add(_chip(t('transfer_bonus'), Icons.transfer_within_a_station_rounded, _accent));
    }
    if (impact != null && impact!.totalCount > 0) {
      final co2 = (impact!.totalCount * 0.03).toStringAsFixed(2);
      chips.add(_chip(
        '${t('co2')} ${co2}kg',
        Icons.eco_rounded,
        const Color(0xFF4ADE80),
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

  Widget _chip(String text, IconData icon, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 12),
            const SizedBox(width: 5),
            Text(text,
                style: TextStyle(
                    color: color,
                    fontSize: 11,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      );
}

// ══════════════════════════════════════════════════════
// 6. 도착 알림 트리거 (진동 + HapticFeedback)
// ══════════════════════════════════════════════════════
Future<void> triggerArrivalAlert() async {
  HapticFeedback.heavyImpact();
  try {
    final hasVib = await Vibration.hasVibrator();
    if (hasVib == true) {
      Vibration.vibrate(pattern: [0, 400, 200, 400, 200, 800]);
    }
  } catch (_) {}
}

// ══════════════════════════════════════════════════════
// 7. 지도 카드 (MapLibre GL — 웹앱 동일 스타일 + 2D/3D 토글 + GPS dot)
// ══════════════════════════════════════════════════════
class MapCard extends StatefulWidget {
  final double currentLat;
  final double currentLon;
  final String currentStation;
  final String? destStation;
  final double? destLat;
  final double? destLon;

  const MapCard({
    super.key,
    required this.currentLat,
    required this.currentLon,
    required this.currentStation,
    this.destStation,
    this.destLat,
    this.destLon,
  });

  @override
  State<MapCard> createState() => _MapCardState();
}

class _MapCardState extends State<MapCard> {
  MapLibreMapController? _ctrl;
  bool _is3D = true;
  bool _styleLoaded = false;

  static const _styleUrl =
      'https://tiles.openfreemap.org/styles/liberty';

  @override
  void didUpdateWidget(MapCard old) {
    super.didUpdateWidget(old);
    if (!_styleLoaded) return;
    final stationMoved = old.currentLat != widget.currentLat ||
        old.currentLon != widget.currentLon;
    final destChanged = old.destLat != widget.destLat ||
        old.destLon != widget.destLon ||
        old.destStation != widget.destStation;
    if (stationMoved || destChanged) _refreshMarkers();
    if (stationMoved) _recenter();
  }

  Future<void> _onStyleLoaded() async {
    _styleLoaded = true;
    await _refreshMarkers();
  }

  Future<void> _refreshMarkers() async {
    final ctrl = _ctrl;
    if (ctrl == null) return;

    for (final id in [
      'label-dest', 'circle-dest', 'label-current', 'circle-current'
    ]) {
      try { await ctrl.removeLayer(id); } catch (_) {}
    }
    for (final id in ['station-dest', 'station-current']) {
      try { await ctrl.removeSource(id); } catch (_) {}
    }

    await ctrl.addGeoJsonSource('station-current', {
      'type': 'FeatureCollection',
      'features': [
        {
          'type': 'Feature',
          'properties': {'name': widget.currentStation},
          'geometry': {
            'type': 'Point',
            'coordinates': [widget.currentLon, widget.currentLat],
          },
        },
      ],
    });
    await ctrl.addCircleLayer(
      'station-current',
      'circle-current',
      CircleLayerProperties(
        circleRadius: 8,
        circleColor: '#7DD3D3',
        circleStrokeWidth: 2.0,
        circleStrokeColor: '#FFFFFF',
      ),
    );
    await ctrl.addSymbolLayer(
      'station-current',
      'label-current',
      SymbolLayerProperties(
        textField: '{name}',
        textSize: 11.0,
        textColor: '#E8EDF5',
        textHaloColor: '#04060A',
        textHaloWidth: 1.5,
        textOffset: [0.0, 1.8],
        textAnchor: 'top',
      ),
    );

    if (widget.destLat != null && widget.destLon != null) {
      await ctrl.addGeoJsonSource('station-dest', {
        'type': 'FeatureCollection',
        'features': [
          {
            'type': 'Feature',
            'properties': {'name': widget.destStation ?? ''},
            'geometry': {
              'type': 'Point',
              'coordinates': [widget.destLon!, widget.destLat!],
            },
          },
        ],
      });
      await ctrl.addCircleLayer(
        'station-dest',
        'circle-dest',
        CircleLayerProperties(
          circleRadius: 8,
          circleColor: '#F0B46A',
          circleStrokeWidth: 2.0,
          circleStrokeColor: '#FFFFFF',
        ),
      );
      await ctrl.addSymbolLayer(
        'station-dest',
        'label-dest',
        SymbolLayerProperties(
          textField: '{name}',
          textSize: 11.0,
          textColor: '#F0B46A',
          textHaloColor: '#04060A',
          textHaloWidth: 1.5,
          textOffset: [0.0, 1.8],
          textAnchor: 'top',
        ),
      );
    }
  }

  Future<void> _toggle3D() async {
    setState(() => _is3D = !_is3D);
    final ctrl = _ctrl;
    if (ctrl == null) return;
    final pos = ctrl.cameraPosition;
    await ctrl.animateCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(
          target:
              pos?.target ?? LatLng(widget.currentLat, widget.currentLon),
          zoom: pos?.zoom ?? 14.0,
          tilt: _is3D ? 50.0 : 0.0,
          bearing: _is3D ? -10.0 : 0.0,
        ),
      ),
    );
  }

  Future<void> _recenter() async {
    final ctrl = _ctrl;
    if (ctrl == null) return;
    await ctrl.animateCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(
          target: LatLng(widget.currentLat, widget.currentLon),
          zoom: 14.0,
          tilt: _is3D ? 50.0 : 0.0,
          bearing: _is3D ? -10.0 : 0.0,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasDest = widget.destStation != null &&
        widget.destLat != null &&
        widget.destLon != null;

    return _cardWrap(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.map_rounded, color: _accent, size: 14),
              const SizedBox(width: 6),
              Text(
                _is3D ? '3D ${t("map")}' : '2D ${t("map")}',
                style: const TextStyle(
                    color: _muted, fontSize: 11, letterSpacing: 1.2),
              ),
              const Spacer(),
              GestureDetector(
                onTap: _recenter,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0x10FFFFFF),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: _line),
                  ),
                  child: const Text('📍',
                      style: TextStyle(fontSize: 12)),
                ),
              ),
              const SizedBox(width: 6),
              GestureDetector(
                onTap: _toggle3D,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: _is3D
                        ? _accent.withValues(alpha: 0.15)
                        : const Color(0x10FFFFFF),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: _is3D
                          ? _accent.withValues(alpha: 0.45)
                          : _line,
                    ),
                  ),
                  child: Text(
                    _is3D ? '2D' : '3D',
                    style: TextStyle(
                      color: _is3D ? _accent : _muted,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
              if (hasDest) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _warn.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(
                        color: _warn.withValues(alpha: 0.35)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.navigation_rounded,
                          color: _warn, size: 10),
                      const SizedBox(width: 4),
                      Text(widget.destStation!,
                          style: const TextStyle(
                              color: _warn,
                              fontSize: 10,
                              fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: SizedBox(
              height: 200,
              child: MapLibreMap(
                styleString: _styleUrl,
                initialCameraPosition: CameraPosition(
                  target: LatLng(widget.currentLat, widget.currentLon),
                  zoom: hasDest ? 12.0 : 14.0,
                  tilt: 50.0,
                  bearing: -10.0,
                ),
                myLocationEnabled: true,
                myLocationTrackingMode: MyLocationTrackingMode.none,
                onMapCreated: (ctrl) => _ctrl = ctrl,
                onStyleLoadedCallback: _onStyleLoaded,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _legend(_accent, widget.currentStation),
              if (hasDest) ...[
                const SizedBox(width: 12),
                _legend(_warn, widget.destStation!),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _legend(Color color, String label) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 10)),
        ],
      );
}
