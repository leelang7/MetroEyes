// MetroEyes — 차량-비특화 시뮬 엔진
// 머리+어깨 벡터 트래킹, 5상태 머신(SIT/STD/BRD/ALG/EXT), 정차 사이클, 흐름 입자.
// 차량별 특수성(레이아웃, 장식, 정원, 사이클 길이)은 createSim 옵션으로 주입.

(function (global) {
  'use strict';

  const ST = { SIT: 'sit', STD: 'std', BRD: 'brd', ALG: 'alg', EXT: 'ext' };

  // ============== 수학/색 헬퍼 ==============
  const lerp = (a, b, t) => [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t];
  const rgba = (c, a) => `rgba(${c[0]|0},${c[1]|0},${c[2]|0},${a})`;
  const angLerp = (a, b, t) => {
    let d = ((b - a + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    return a + d * t;
  };
  const occColor = (o) => {
    if (o < 0.4) return [232, 237, 245];
    if (o < 0.7) return lerp([232,237,245], [240,180,106], (o-0.4)/0.3);
    if (o < 0.9) return lerp([240,180,106], [255,108,90], (o-0.7)/0.2);
    return [255, 94, 87];
  };
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }

  // ============== 캔버스 헬퍼 ==============
  function fitCanvas(c) {
    const r = c.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return null;
    c.width = Math.round(r.width * devicePixelRatio);
    c.height = Math.round(r.height * devicePixelRatio);
    const ctx = c.getContext('2d');
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    return { ctx, W: r.width, H: r.height };
  }
  function rrect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // ============== Passenger ==============
  let _pid = 1;
  function makePassenger(opts) {
    return {
      id: _pid++,
      x: opts.x, y: opts.y,
      vx: 0, vy: 0,
      heading: opts.heading ?? 0,
      state: opts.state,
      target: opts.target ?? null,
      seat: opts.seat ?? null,
      fade: opts.fade ?? (opts.state === ST.BRD ? 0 : 1),
      age: Math.random() * 3,
      bobPhase: Math.random() * Math.PI * 2,
      color: opts.color ?? (opts.state === ST.SIT ? [154, 166, 185] : [232, 237, 245]),
      flag: null,         // 'emergency' | 'suspicious' | null
      flagT: 0,           // 플래그 지속 시간
    };
  }
  function steerToward(p, dt, speed = 56, arrival = 7, slowDist = 14) {
    if (!p.target) return false;
    const dx = p.target.x - p.x, dy = p.target.y - p.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 1.2) return true;
    const ts = dist < slowDist ? speed * (dist / slowDist) : speed;
    const dvx = (dx / dist) * ts - p.vx;
    const dvy = (dy / dist) * ts - p.vy;
    const k = Math.min(1, dt * arrival);
    p.vx += dvx * k;
    p.vy += dvy * k;
    return false;
  }
  function separate(p, others, dt, radius = 11, force = 60) {
    let ax = 0, ay = 0, n = 0;
    for (const o of others) {
      if (o === p || o.state === ST.SIT || o.fade < 0.3) continue;
      const dx = p.x - o.x, dy = p.y - o.y;
      const d = Math.hypot(dx, dy);
      if (d > 0 && d < radius) {
        ax += (dx / d) * (1 - d / radius);
        ay += (dy / d) * (1 - d / radius);
        n++;
      }
    }
    if (n > 0) {
      p.vx += ax * force * dt;
      p.vy += ay * force * dt;
    }
  }

  // role: 'board' | 'alight' | 'both' | undefined(='both')
  function doorsByRole(layout, role) {
    const filtered = layout.doors.filter(d => !d.role || d.role === 'both' || d.role === role);
    return filtered.length > 0 ? filtered : layout.doors;
  }
  function nearestDoorByRole(p, layout, role) {
    const pool = doorsByRole(layout, role);
    let best = pool[0], bd = Infinity;
    for (const d of pool) {
      const dd = Math.hypot(d.x - p.x, d.y - p.y);
      if (dd < bd) { bd = dd; best = d; }
    }
    return best;
  }
  function pickInteriorTarget(layout, reservedSeatIdx, preferSeat = true) {
    if (preferSeat) {
      const empties = [];
      for (let i = 0; i < layout.seats.length; i++) {
        if (!reservedSeatIdx.has(i)) empties.push(i);
      }
      if (empties.length > 0) {
        const idx = empties[Math.floor(Math.random() * empties.length)];
        const s = layout.seats[idx];
        return { x: s.x, y: s.y, type: 'seat', seat: s, seatIdx: idx };
      }
    }
    const ax = layout.pad + (layout.gap ?? 8) + 6 + Math.random() * (layout.cw - (layout.gap ?? 8) * 2 - 12);
    const ay = layout.pad + layout.ch / 2 + (Math.random() - 0.5) * layout.ch * 0.22;
    return { x: ax, y: ay, type: 'aisle' };
  }

  function drawPerson(ctx, p, hi) {
    let c = p.color;
    if (p.flag === 'emergency') c = [255, 94, 87];
    else if (p.flag === 'suspicious') c = [240, 180, 106];
    else if (p.state === ST.ALG || p.state === ST.EXT) c = [240, 150, 110];
    else if (p.state === ST.BRD) c = [180, 220, 230];
    else if (hi && p.state !== ST.SIT) c = [240, 180, 106];

    const sp = Math.hypot(p.vx, p.vy);
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.heading);

    // 진행 방향 예측선 (Tesla 스타일)
    if (sp > 14 && p.fade > 0.4) {
      const ahead = Math.min(22, sp * 0.32);
      ctx.strokeStyle = rgba(c, 0.20 * p.fade);
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.moveTo(5, 0);
      ctx.lineTo(5 + ahead, 0);
      ctx.stroke();
    }
    // 모션 트레일
    if (sp > 10 && p.fade > 0.5) {
      ctx.fillStyle = rgba(c, 0.13 * p.fade);
      ctx.beginPath();
      ctx.ellipse(-7, 0, 9, 4, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    // 응급환자: 누워있는 자세로 길쭉하게 그림
    const isEmer = p.flag === 'emergency';
    const shoulderW = isEmer ? 18 : 12.4;
    const shoulderH = isEmer ? 4.5 : 6.4;
    // 어깨
    ctx.shadowColor = rgba(c, 0.38);
    ctx.shadowBlur = 4;
    ctx.fillStyle = rgba(c, 0.5 * p.fade);
    rrect(ctx, -shoulderW / 2, -shoulderH / 2, shoulderW, shoulderH, 2.6);
    ctx.fill();
    // 머리
    ctx.shadowBlur = 7;
    ctx.fillStyle = rgba(c, 0.96 * p.fade);
    ctx.beginPath();
    ctx.arc(isEmer ? shoulderW / 2 : 2.6, 0, 3.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 플래그 펄스 링 (월드 좌표계로 다시 그림)
    if (p.flag) {
      const t = (performance.now() / 1000) % 1;
      const ringC = p.flag === 'emergency' ? [255, 94, 87] : [240, 170, 90];
      ctx.save();
      for (let i = 0; i < 2; i++) {
        const phase = (t + i * 0.5) % 1;
        const r = 9 + phase * 18;
        ctx.strokeStyle = rgba(ringC, 0.55 * (1 - phase));
        ctx.lineWidth = 1.3;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  function drawLostItem(ctx, item) {
    const t = (performance.now() / 1000) % 1;
    ctx.save();
    // 박스형 객체
    ctx.fillStyle = 'rgba(154, 166, 185, 0.28)';
    ctx.strokeStyle = 'rgba(240, 180, 106, 0.55)';
    ctx.lineWidth = 1;
    rrect(ctx, item.x - 5, item.y - 5, 10, 10, 2);
    ctx.fill(); ctx.stroke();
    // 펄스 링
    for (let i = 0; i < 2; i++) {
      const phase = (t + i * 0.5) % 1;
      const r = 8 + phase * 16;
      ctx.strokeStyle = `rgba(240, 180, 106, ${0.45 * (1 - phase)})`;
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.arc(item.x, item.y, r, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  // ============== createSim ==============
  function createSim(config) {
    const {
      canvas,
      capacity,
      cycleDur = { arriving: 1.8, stopped: 5.5, departing: 1.8, running: 4.5 },
      layoutFn,
      decorate = null,
      overlay = null,
      compact = false,
      pad = 14,
      bgColor = '#0c1018',
      headingLabel = '← 진행',
      enableSafetyDetection = false,   // 멀티태스크 안전 감지 ON/OFF
      onIncident = null,                // (incident) => {} 콜백
      safetyMeanInterval = 14,          // 평균 N초마다 사건 발생 시도
    } = config;

    const sim = {
      capacity,
      layout: null,
      passengers: [],
      occ: 0.5,
      targetCount: Math.round(capacity * 0.5),
      cyclePhase: 'stopped',
      cycleT: 1.5,
      phaseDur: cycleDur,
      doorAlpha: 0.95,
      flowParticles: [],
      swayPhase: 0,
      lostItems: [],                       // [{ x, y, ts, seatIdx? }]
      safetyT: 0,
      safetyMetrics: { freeRideEst: 0, _accumBoardCount: 0 },
      _incidentSeq: 1,
    };

    function bootstrapPassengers(occ) {
      sim.passengers = [];
      const target = Math.round(capacity * occ);
      const seatN = Math.min(sim.layout.seats.length, target);
      const standN = Math.max(0, target - seatN);
      const seatIdx = [...sim.layout.seats.keys()];
      shuffle(seatIdx);
      for (let i = 0; i < seatN; i++) {
        const s = sim.layout.seats[seatIdx[i]];
        const heading = s.side === 0 ? Math.PI / 2 : -Math.PI / 2;
        sim.passengers.push(makePassenger({
          x: s.x, y: s.y, heading, state: ST.SIT, seat: s, fade: 1,
        }));
      }
      const boardDoors = doorsByRole(sim.layout, 'board');
      for (let i = 0; i < standN; i++) {
        const door = boardDoors[Math.floor(Math.random() * boardDoors.length)];
        const ax = door.x + (Math.random() - 0.5) * sim.layout.cw * 0.18;
        const ay = sim.layout.pad + sim.layout.ch * (0.42 + Math.random() * 0.16);
        sim.passengers.push(makePassenger({
          x: ax, y: ay, heading: Math.random() * Math.PI * 2, state: ST.STD, fade: 1,
        }));
      }
      sim.targetCount = target;
    }

    function setTargetOccupancy(occ) {
      sim.occ = occ;
      sim.targetCount = Math.round(capacity * occ);
    }

    function reservedSeatIndices() {
      const reserved = new Set();
      for (const p of sim.passengers) {
        if (p.fade <= 0) continue;
        if (p.seat) {
          const i = sim.layout.seats.indexOf(p.seat);
          if (i >= 0) reserved.add(i);
        } else if (p.state === ST.BRD && p.target?.type === 'seat' && typeof p.target.seatIdx === 'number') {
          reserved.add(p.target.seatIdx);
        }
      }
      return reserved;
    }

    function liveCount() {
      return sim.passengers.filter(p => p.state !== ST.EXT && p.fade > 0.05).length;
    }

    function triggerBoardingAndAlighting() {
      const cur = liveCount();
      const next = sim.targetCount;
      const turnover = Math.round(cur * (0.25 + Math.random() * 0.20));
      const alightN = Math.min(cur, turnover);
      const boardN = Math.max(0, alightN + (next - cur));

      const sitters = sim.passengers.filter(p => p.state === ST.SIT);
      const standers = sim.passengers.filter(p => p.state === ST.STD);
      shuffle(sitters); shuffle(standers);
      let sitTake = Math.min(sitters.length, Math.round(alightN * 0.6));
      let stdTake = Math.min(standers.length, alightN - sitTake);
      if (sitTake + stdTake < alightN) sitTake = Math.min(sitters.length, alightN - stdTake);

      for (const p of sitters.slice(0, sitTake).concat(standers.slice(0, stdTake))) {
        const door = nearestDoorByRole(p, sim.layout, 'alight');
        p.state = ST.ALG;
        p.target = { x: door.x + (Math.random() - 0.5) * 6, y: door.y, type: 'door', door };
        if (p.seat) p.seat = null;
        p.color = [216, 168, 138];
      }

      const reserved = reservedSeatIndices();
      const boardDoors = doorsByRole(sim.layout, 'board');
      for (let i = 0; i < boardN; i++) {
        const door = boardDoors[Math.floor(Math.random() * boardDoors.length)];
        const sign = door.side === 'top' ? -1 : 1;
        const sx = door.x + (Math.random() - 0.5) * 18;
        const sy = door.y + sign * (16 + Math.random() * 14);
        const preferSeat = Math.random() < 0.78;
        const target = pickInteriorTarget(sim.layout, reserved, preferSeat);
        if (target.type === 'seat') reserved.add(target.seatIdx);
        sim.passengers.push(makePassenger({
          x: sx, y: sy, heading: -sign * Math.PI / 2,
          state: ST.BRD, target, fade: 0,
          color: [220, 232, 245],
        }));
      }
    }

    function onPhaseChange(prev, next) {
      if (next === 'stopped') {
        triggerBoardingAndAlighting();
      } else if (next === 'departing') {
        for (const p of sim.passengers) {
          if (p.state === ST.ALG) p.state = ST.EXT;
        }
        // 출발 시점에 분실물 감지 — 좌석에서 막 일어난 사람의 ~3% 확률로 잔존
        if (enableSafetyDetection) {
          const exiters = sim.passengers.filter(p => p.state === ST.EXT);
          for (const p of exiters) {
            if (Math.random() < 0.04) {
              const lx = p.x + (Math.random() - 0.5) * 4;
              const ly = p.y + (Math.random() - 0.5) * 4;
              const item = { x: lx, y: ly, ts: performance.now() };
              sim.lostItems.push(item);
              emitIncident({
                type: 'lost', severity: 'low',
                x: lx, y: ly,
                msg: '잔존 박스형 객체 감지',
              });
            }
          }
        }
      }
    }

    function emitIncident(ev) {
      const incident = {
        id: sim._incidentSeq++,
        ts: performance.now(),
        ...ev,
      };
      if (onIncident) onIncident(incident);
    }

    function trySpawnIncident() {
      // 어떤 사건? 응급(40) / 이상행동(35) / 무임승차(25)
      const r = Math.random();
      if (r < 0.40) spawnEmergency();
      else if (r < 0.75) spawnSuspicious();
      else spawnFreeRide();
    }

    function spawnEmergency() {
      const sitters = sim.passengers.filter(p => p.state === ST.SIT && !p.flag);
      if (sitters.length === 0) return;
      const p = sitters[Math.floor(Math.random() * sitters.length)];
      p.flag = 'emergency';
      p.flagT = 14;       // 14초간 지속
      // 머리 방향 누운 자세 (heading 0 또는 PI)
      p.heading = Math.random() < 0.5 ? 0 : Math.PI;
      emitIncident({
        type: 'emergency', severity: 'high',
        x: p.x, y: p.y, passengerId: p.id,
        msg: '응급환자 감지 — 비정상 자세 (누움)',
      });
    }

    function spawnSuspicious() {
      const standers = sim.passengers.filter(p => p.state === ST.STD && !p.flag);
      if (standers.length < 2) return;
      // 두 명 가까이 있는 페어 찾기
      shuffle(standers);
      let pair = null;
      for (let i = 0; i < standers.length; i++) {
        for (let j = i + 1; j < standers.length; j++) {
          if (Math.hypot(standers[i].x - standers[j].x, standers[i].y - standers[j].y) < 30) {
            pair = [standers[i], standers[j]];
            break;
          }
        }
        if (pair) break;
      }
      if (!pair) return;
      pair.forEach(p => { p.flag = 'suspicious'; p.flagT = 8; });
      const cx = (pair[0].x + pair[1].x) / 2;
      const cy = (pair[0].y + pair[1].y) / 2;
      emitIncident({
        type: 'suspicious', severity: 'med',
        x: cx, y: cy,
        msg: '이상행동 감지 — 비정상 거리 변화 패턴',
      });
    }

    function spawnFreeRide() {
      // 집계: 누적 BRD vs 추정 카드 태그 차이
      // 단순 시뮬: 0.5~3건 사이 랜덤 추가
      const n = 1 + Math.floor(Math.random() * 3);
      sim.safetyMetrics.freeRideEst += n;
      emitIncident({
        type: 'free_ride', severity: 'low',
        msg: `무임승차 추정 +${n}건 — 출입 vs 카드 태그 갭`,
      });
    }

    function updateSafety(dt) {
      if (!enableSafetyDetection) return;
      sim.safetyT += dt;
      const interval = safetyMeanInterval;
      // Poisson-ish: 매 dt당 dt/interval 확률로 트리거
      if (Math.random() < dt / interval) {
        sim.safetyT = 0;
        trySpawnIncident();
      }
      // 플래그 타임아웃
      for (const p of sim.passengers) {
        if (p.flag) {
          p.flagT -= dt;
          if (p.flagT <= 0) {
            p.flag = null;
          }
        }
      }
      // 분실물 자연 감쇠 (~30초 후 사라짐)
      const now = performance.now();
      sim.lostItems = sim.lostItems.filter(it => now - it.ts < 30000);
    }

    function updateCycle(dt) {
      sim.cycleT += dt;
      const dur = sim.phaseDur[sim.cyclePhase];
      if (sim.cycleT >= dur) {
        sim.cycleT = 0;
        const next = { arriving: 'stopped', stopped: 'departing', departing: 'running', running: 'arriving' };
        const prev = sim.cyclePhase;
        sim.cyclePhase = next[prev];
        onPhaseChange(prev, sim.cyclePhase);
      }
      let target = 0;
      if (sim.cyclePhase === 'stopped') target = 1;
      else if (sim.cyclePhase === 'arriving') target = sim.cycleT / dur;
      else if (sim.cyclePhase === 'departing') target = 1 - sim.cycleT / dur;
      sim.doorAlpha += (target - sim.doorAlpha) * Math.min(1, dt * 5);
      sim.swayPhase += dt * (sim.cyclePhase === 'running' ? 1.6 : 0.4);
    }

    function updatePassengers(dt) {
      const others = sim.passengers;
      for (const p of sim.passengers) {
        p.age += dt;
        if (p.state === ST.EXT) {
          p.fade = Math.max(0, p.fade - dt * 1.6);
        } else if (p.fade < 1) {
          p.fade = Math.min(1, p.fade + dt * 1.6);
        }

        if (p.state === ST.SIT) {
          const wob = Math.sin(p.age * 1.4 + p.bobPhase) * 0.045;
          const baseHeading = p.seat ? (p.seat.side === 0 ? Math.PI / 2 : -Math.PI / 2) : 0;
          p.heading = baseHeading + wob;
          p.vx *= 0.5; p.vy *= 0.5;
          continue;
        }
        if (p.state === ST.STD) {
          const swayAmp = sim.cyclePhase === 'running' ? 7 : 2;
          const swayX = Math.sin(sim.swayPhase + p.bobPhase) * swayAmp;
          p.vx += (swayX - p.vx) * Math.min(1, dt * 1.2);
          p.vy += -p.vy * Math.min(1, dt * 1.5);
          p.vx += (Math.random() - 0.5) * 4;
          p.vy += (Math.random() - 0.5) * 2;
          separate(p, others, dt, 11, 50);
        } else if (p.state === ST.BRD) {
          const arrived = steerToward(p, dt, 52, 6);
          separate(p, others, dt, 10, 60);
          if (arrived) {
            if (p.target?.type === 'seat' && p.target.seat) {
              p.seat = p.target.seat;
              p.state = ST.SIT;
              p.x = p.seat.x; p.y = p.seat.y;
              p.color = [154, 166, 185];
            } else {
              p.state = ST.STD;
            }
            p.target = null;
          }
        } else if (p.state === ST.ALG) {
          const arrived = steerToward(p, dt, 60, 7);
          separate(p, others, dt, 9, 55);
          if (arrived) p.state = ST.EXT;
        } else if (p.state === ST.EXT) {
          const door = p.target?.door;
          if (door) {
            const sign = door.side === 'top' ? -1 : 1;
            p.vy += sign * -22 * dt;
          }
        }

        p.x += p.vx * dt;
        p.y += p.vy * dt;

        if (p.state === ST.STD || p.state === ST.BRD) {
          const minX = sim.layout.pad + 6, maxX = sim.layout.pad + sim.layout.cw - 6;
          const minY = sim.layout.pad + (sim.layout.sh ?? 12) + 4;
          const maxY = sim.layout.pad + sim.layout.ch - (sim.layout.sh ?? 12) - 4;
          if (p.x < minX) { p.x = minX; p.vx *= -0.4; }
          if (p.x > maxX) { p.x = maxX; p.vx *= -0.4; }
          if (p.y < minY) { p.y = minY; p.vy *= -0.4; }
          if (p.y > maxY) { p.y = maxY; p.vy *= -0.4; }
        }
        p.vx *= Math.pow(0.18, dt);
        p.vy *= Math.pow(0.18, dt);

        const sp = Math.hypot(p.vx, p.vy);
        if (sp > 4) {
          const targetH = Math.atan2(p.vy, p.vx);
          p.heading = angLerp(p.heading, targetH, Math.min(1, dt * 8));
        }
      }
      for (let i = sim.passengers.length - 1; i >= 0; i--) {
        const p = sim.passengers[i];
        if (p.state === ST.EXT && p.fade <= 0.02) sim.passengers.splice(i, 1);
      }
    }

    function updateFlowParticles(dt) {
      if (!sim.layout) return;
      if (sim.doorAlpha > 0.35) {
        for (const d of sim.layout.doors) {
          let inbound = 0, outbound = 0;
          for (const p of sim.passengers) {
            const near = Math.hypot(p.x - d.x, p.y - d.y) < 42;
            if (!near) continue;
            if (p.state === ST.BRD) inbound++;
            else if (p.state === ST.ALG) outbound++;
          }
          const sign = d.side === 'top' ? -1 : 1;
          const role = d.role || 'both';
          if ((role === 'board' || role === 'both') && Math.random() < dt * (0.4 + inbound * 0.3)) {
            sim.flowParticles.push({
              x: d.x + (Math.random() - 0.5) * 14,
              y: d.y + sign * (8 + Math.random() * 6),
              vx: (Math.random() - 0.5) * 4, vy: -sign * 28,
              life: 0.6, maxLife: 0.6, dir: 'in',
            });
          }
          if ((role === 'alight' || role === 'both') && Math.random() < dt * (outbound * 0.5)) {
            sim.flowParticles.push({
              x: d.x + (Math.random() - 0.5) * 8,
              y: d.y + (-sign) * 4,
              vx: (Math.random() - 0.5) * 3, vy: sign * 28,
              life: 0.55, maxLife: 0.55, dir: 'out',
            });
          }
        }
      }
      for (const fp of sim.flowParticles) {
        fp.x += fp.vx * dt; fp.y += fp.vy * dt; fp.life -= dt;
      }
      sim.flowParticles = sim.flowParticles.filter(fp => fp.life > 0);
    }

    function drawFlowParticles(ctx) {
      for (const fp of sim.flowParticles) {
        const a = (fp.life / fp.maxLife) * sim.doorAlpha;
        const c = fp.dir === 'in' ? [125, 211, 211] : [240, 170, 130];
        ctx.fillStyle = rgba(c, 0.55 * a);
        ctx.beginPath();
        ctx.arc(fp.x, fp.y, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function drawDoors(ctx, L) {
      const da = sim.doorAlpha;
      ctx.save();
      for (const d of L.doors) {
        const halfW = 26;
        const gap = 8 * da;
        const role = d.role || 'both';
        const cc = role === 'alight' ? [240, 170, 130] : [125, 211, 211];
        ctx.shadowColor = rgba(cc, 0.3 + da * 0.4);
        ctx.shadowBlur = 6 + da * 14;
        ctx.fillStyle = rgba(cc, 0.42 + da * 0.5);
        ctx.fillRect(d.x - halfW, d.y - 1.5, halfW - gap, 3);
        ctx.fillRect(d.x + gap, d.y - 1.5, halfW - gap, 3);
      }
      ctx.restore();
    }

    function ensureLayout() {
      const fitted = fitCanvas(canvas);
      if (!fitted) return null;
      sim._fit = fitted;
      if (!sim.layout || sim.layout.W !== fitted.W || sim.layout.H !== fitted.H) {
        sim.layout = { ...layoutFn(fitted.W, fitted.H, pad), W: fitted.W, H: fitted.H };
        if (sim.passengers.length === 0) bootstrapPassengers(sim.occ);
      }
      return fitted;
    }

    function drawBev() {
      const fitted = ensureLayout();
      if (!fitted) return;
      const { ctx, W, H } = fitted;
      const L = sim.layout;
      ctx.clearRect(0, 0, W, H);

      // 외곽 + heat
      rrect(ctx, L.pad, L.pad, L.cw, L.ch, 18);
      ctx.fillStyle = bgColor; ctx.fill();
      if (sim.occ > 0.3) {
        const heat = Math.min(1, (sim.occ - 0.3) / 0.7);
        ctx.fillStyle = rgba(occColor(sim.occ), 0.05 + heat * 0.07);
        ctx.fill();
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = 1;
      rrect(ctx, L.pad + 0.5, L.pad + 0.5, L.cw - 1, L.ch - 1, 18);
      ctx.stroke();

      // 좌석 슬롯
      const seatOccupied = new Set();
      for (const p of sim.passengers) {
        if (p.state === ST.SIT && p.seat) seatOccupied.add(L.seats.indexOf(p.seat));
        else if (p.state === ST.BRD && p.target?.type === 'seat' && typeof p.target.seatIdx === 'number') {
          seatOccupied.add(p.target.seatIdx);
        }
      }
      for (let i = 0; i < L.seats.length; i++) {
        const s = L.seats[i];
        const occupied = seatOccupied.has(i);
        ctx.fillStyle = occupied ? 'rgba(154, 166, 185, 0.10)' : 'rgba(255,255,255,0.025)';
        rrect(ctx, s.x - 7, s.y - 7, 14, 14, 3);
        ctx.fill();
        if (s.priority) {
          ctx.strokeStyle = 'rgba(125, 211, 211, 0.18)';
          rrect(ctx, s.x - 7, s.y - 7, 14, 14, 3);
          ctx.stroke();
        }
      }

      // 차량별 장식 (운전석 등)
      if (decorate) decorate(ctx, L, sim);

      drawDoors(ctx, L);
      drawFlowParticles(ctx);

      // 분실물
      for (const it of sim.lostItems) drawLostItem(ctx, it);

      const isHi = sim.occ > 0.85;
      const order = { sit: 0, std: 1, brd: 2, alg: 3, ext: 4 };
      const sorted = [...sim.passengers].sort((a, b) => order[a.state] - order[b.state]);
      for (const p of sorted) drawPerson(ctx, p, isHi);

      // 페이지별 오버레이 (사용자 위치 마커 등)
      if (overlay) overlay(ctx, L, sim);

      if (compact) return;

      // 텔레메트리 (좌상단: 객체 카운트)
      let nSit = 0, nStd = 0, nBrd = 0, nAlg = 0;
      for (const p of sim.passengers) {
        if (p.fade < 0.3) continue;
        if (p.state === ST.SIT) nSit++;
        else if (p.state === ST.STD) nStd++;
        else if (p.state === ST.BRD) nBrd++;
        else if (p.state === ST.ALG) nAlg++;
      }
      ctx.font = '500 10px Inter, "Malgun Gothic", system-ui';
      const stats = [
        ['SIT', nSit, [154, 166, 185]],
        ['STD', nStd, [232, 237, 245]],
        ['BRD', `+${nBrd}`, [125, 211, 211]],
        ['ALG', `-${nAlg}`, [240, 170, 130]],
      ];
      let sx = L.pad + 16;
      ctx.textBaseline = 'middle';
      for (const [k, v, cc] of stats) {
        ctx.fillStyle = rgba(cc, 0.55);
        ctx.fillText(k, sx, L.pad + 14);
        ctx.fillStyle = rgba(cc, 1);
        ctx.fillText(String(v), sx + 24, L.pad + 14);
        sx += 60;
      }
      ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = 'rgba(107, 118, 138, 0.9)';
      ctx.fillText(headingLabel, L.pad + 16, L.pad + L.ch - 14);

      // 우상단: 점유율 + 페이즈
      ctx.font = '500 11px Inter, "Malgun Gothic", system-ui';
      ctx.fillStyle = '#e8edf5';
      const occLabel = `${Math.round(sim.occ * 100)}% · ${liveCount()}명`;
      ctx.fillText(occLabel, L.pad + L.cw - 16 - ctx.measureText(occLabel).width, L.pad + 16);
      const phaseText = { arriving: '도착 중', stopped: '정차', departing: '출발', running: '운행' }[sim.cyclePhase];
      ctx.fillStyle = sim.cyclePhase === 'stopped' ? 'rgba(125, 211, 211, 0.85)' : 'rgba(107, 118, 138, 0.9)';
      ctx.font = '500 10px Inter';
      ctx.fillText(phaseText, L.pad + L.cw - 16 - ctx.measureText(phaseText).width, L.pad + 32);
    }

    function tick(dt) {
      if (!ensureLayout()) return;
      updateCycle(dt);
      updatePassengers(dt);
      updateFlowParticles(dt);
      updateSafety(dt);
      drawBev();
    }

    function forceRebuild(occ) {
      if (occ != null) sim.occ = occ;
      sim.passengers.length = 0;
      sim.flowParticles.length = 0;
      sim.cyclePhase = 'stopped';
      sim.cycleT = 0.8;
      sim.doorAlpha = 0.95;
    }

    function invalidateLayout() {
      sim.layout = null;
      sim.passengers.length = 0;
      sim.flowParticles.length = 0;
    }

    function stats() {
      let nSit = 0, nStd = 0, nBrd = 0, nAlg = 0;
      for (const p of sim.passengers) {
        if (p.fade < 0.3) continue;
        if (p.state === ST.SIT) nSit++;
        else if (p.state === ST.STD) nStd++;
        else if (p.state === ST.BRD) nBrd++;
        else if (p.state === ST.ALG) nAlg++;
      }
      return { sit: nSit, std: nStd, brd: nBrd, alg: nAlg };
    }

    function priorityStats() {
      // 약자석(priority)에 앉은 사람 수, 약자석 근처에 입석 차단 여부
      if (!sim.layout) return { occupied: 0, total: 0, blocked: 0 };
      let occ = 0, blocked = 0;
      const prioritySeats = sim.layout.seats.map((s, i) => s.priority ? i : -1).filter(i => i >= 0);
      for (const p of sim.passengers) {
        if (p.state === ST.SIT && p.seat?.priority) occ++;
      }
      // blocked: 약자석 인근에 입석 사람이 있으면 (휠체어/유아차 공간 차단으로 해석)
      for (const idx of prioritySeats) {
        const s = sim.layout.seats[idx];
        for (const p of sim.passengers) {
          if (p.state === ST.STD && Math.hypot(p.x - s.x, p.y - s.y) < 16) {
            blocked++;
            break;
          }
        }
      }
      return { occupied: occ, total: prioritySeats.length, blocked };
    }

    function getLostItems() { return sim.lostItems.slice(); }
    function clearLostItem(idx) {
      if (idx >= 0 && idx < sim.lostItems.length) sim.lostItems.splice(idx, 1);
    }
    function getSafetyMetrics() { return { ...sim.safetyMetrics }; }
    function clearEmergencyFlags() {
      for (const p of sim.passengers) {
        if (p.flag) p.flag = null;
      }
      sim.lostItems = [];
    }

    return {
      tick,
      setTargetOccupancy,
      forceRebuild,
      invalidateLayout,
      liveCount,
      stats,
      priorityStats,
      getLostItems,
      clearLostItem,
      getSafetyMetrics,
      clearEmergencyFlags,
      getPhase: () => sim.cyclePhase,
      getOccupancy: () => sim.occ,
      getCapacity: () => capacity,
      getLayout: () => sim.layout,
      _sim: sim,
    };
  }

  // ============== Vehicle layouts ==============
  // 도시철도 차량 — 양 측면에 좌석 블록 6개, 출입문 4쌍 (양측 페어)
  function subwayLayout(W, H, pad) {
    const SEAT_BLOCKS = 6, SEATS_PER_BLOCK = 7;
    const DOORS_X = [0.18, 0.42, 0.58, 0.82];
    const cw = W - pad * 2, ch = H - pad * 2;
    const gap = 10;
    const bw = (cw - (SEAT_BLOCKS + 1) * gap) / SEAT_BLOCKS;
    const sh = ch * 0.18;
    const seats = [];
    for (let side of [0, 1]) {
      const yc = side === 0 ? pad + 10 + sh / 2 : pad + ch - sh - 10 + sh / 2;
      for (let b = 0; b < SEAT_BLOCKS; b++) {
        const bx = pad + gap + b * (bw + gap);
        const isPriority = (b === 0 || b === SEAT_BLOCKS - 1);
        for (let s = 0; s < SEATS_PER_BLOCK; s++) {
          const sx = bx + (s + 0.5) * (bw / SEATS_PER_BLOCK);
          seats.push({ x: sx, y: yc, side, block: b, priority: isPriority });
        }
      }
    }
    const doors = [];
    for (const dx of DOORS_X) {
      const x = pad + dx * cw;
      doors.push({ x, y: pad, side: 'top' });
      doors.push({ x, y: pad + ch, side: 'bottom' });
    }
    return { seats, doors, pad, cw, ch, bw, sh, gap };
  }

  // 시내버스 — 단일 차량, 한 쪽(아래)에만 출입문 2개 (앞문=승차, 뒷문=하차)
  // 좌석: 위쪽 일렬(운전석 측), 아래쪽 도어 사이 + 도어 뒤, 후미 일자형
  function busLayout(W, H, pad) {
    const cw = W - pad * 2, ch = H - pad * 2;
    const gap = 8;
    const sh = ch * 0.20;
    const topY = pad + 10 + sh / 2;
    const bottomY = pad + ch - 10 - sh / 2;
    const seats = [];

    // 위쪽 (운전석 측) — 운전석 뒤로 8석
    const topStart = pad + cw * 0.15;
    const topEnd = pad + cw * 0.92;
    const topN = 8;
    for (let i = 0; i < topN; i++) {
      const x = topStart + (i + 0.5) * (topEnd - topStart) / topN;
      seats.push({ x, y: topY, side: 0, priority: i === 0 });  // 운전석 바로 뒤 = 약자석
    }
    // 아래쪽 — 앞문(0.18)과 뒷문(0.55) 사이 4석 + 뒷문 뒤 4석
    const bot1Start = pad + cw * 0.22, bot1End = pad + cw * 0.50;
    for (let i = 0; i < 4; i++) {
      const x = bot1Start + (i + 0.5) * (bot1End - bot1Start) / 4;
      seats.push({ x, y: bottomY, side: 1, priority: i === 0 });  // 앞문 뒤 = 약자석
    }
    const bot2Start = pad + cw * 0.62, bot2End = pad + cw * 0.92;
    for (let i = 0; i < 4; i++) {
      const x = bot2Start + (i + 0.5) * (bot2End - bot2Start) / 4;
      seats.push({ x, y: bottomY, side: 1, priority: false });
    }
    // 후미 일자형 (뒷자리 가로) — 4석
    const rearX = pad + cw * 0.96;
    const rearN = 4;
    const rearTop = topY, rearBot = bottomY;
    for (let i = 0; i < rearN; i++) {
      const y = rearTop + (i + 0.5) * (rearBot - rearTop) / rearN;
      const side = (y < (topY + bottomY) / 2) ? 0 : 1;
      seats.push({ x: rearX, y, side, priority: false });
    }

    const doors = [
      { x: pad + cw * 0.18, y: pad + ch, side: 'bottom', role: 'board' },   // 앞문
      { x: pad + cw * 0.55, y: pad + ch, side: 'bottom', role: 'alight' },  // 뒷문
    ];

    return { seats, doors, pad, cw, ch, sh, gap, driverPos: { x: pad + cw * 0.05, y: topY } };
  }

  function decorateBus(ctx, L, sim) {
    if (!L.driverPos) return;
    const d = L.driverPos;
    // 복도 바닥 — 위아래 좌석 사이 공간에 연한 색조
    const aisleY = L.pad + L.ch * 0.30;
    const aisleH = L.ch * 0.40;
    const grad = ctx.createLinearGradient(L.pad, aisleY, L.pad, aisleY + aisleH);
    grad.addColorStop(0, 'rgba(180,200,230,0.04)');
    grad.addColorStop(0.5, 'rgba(180,200,230,0.08)');
    grad.addColorStop(1, 'rgba(180,200,230,0.04)');
    ctx.fillStyle = grad;
    ctx.fillRect(L.pad + 4, aisleY, L.cw - 8, aisleH);
    // 운전석 박스
    ctx.save();
    ctx.fillStyle = 'rgba(125, 211, 211, 0.08)';
    ctx.strokeStyle = 'rgba(125, 211, 211, 0.45)';
    ctx.lineWidth = 1;
    rrect(ctx, d.x - 12, d.y - 9, 24, 18, 3);
    ctx.fill(); ctx.stroke();
    ctx.font = '500 8px Inter';
    ctx.fillStyle = 'rgba(125, 211, 211, 0.75)';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('DRV', d.x, d.y);
    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
    ctx.restore();
  }

  // ============== Occupancy 모델 (1주차 EDA 기반) ==============
  const CLUSTERS = {
    office: { am: 0.32, pm: 0.95, base: 0.22, label: '오피스형' },
    resi:   { am: 0.95, pm: 0.45, base: 0.22, label: '주거형' },
    hub:    { am: 0.85, pm: 0.92, base: 0.40, label: '환승 허브' },
  };
  const gauss = (x, mu, s) => Math.exp(-0.5 * ((x - mu) / s) ** 2);
  function trainOccupancyAt(h, k) {
    const c = CLUSTERS[k];
    return Math.min(1.05, c.am * gauss(h, 8, 1.0) + c.pm * gauss(h, 18, 1.2) + c.base * gauss(h, 13, 4) * 0.4);
  }
  function rngSeeded(seed) {
    let s = seed * 9301 + 49297;
    return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
  }
  function carOccupancies(avg, n, seed) {
    const r = rngSeeded(seed);
    return Array.from({ length: n }, (_, i) => {
      const dist = Math.abs(i - (n - 1) / 2) / ((n - 1) / 2);
      const noise = (r() - 0.5) * 0.18;
      return Math.max(0, Math.min(1.1, avg * (1 - dist * 0.55) + noise));
    });
  }

  // ============== Public ==============
  global.BEVEngine = {
    createSim,
    ST,
    occColor,
    rgba,
    rrect,
    fitCanvas,
    layouts: { subway: subwayLayout, bus: busLayout },
    decorators: { bus: decorateBus },
    model: { CLUSTERS, trainOccupancyAt, carOccupancies, gauss },
    render: { drawPerson, drawLostItem },   // 외부 렌더러용 (실 카메라 데이터 등)
  };
})(window);
