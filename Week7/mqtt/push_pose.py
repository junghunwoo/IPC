#!/usr/bin/env python3
"""노트북에서 MQTT 브로커에 '자세' 메시지를 push 하는 최소 스크립트 (paho-mqtt).

사용법
  pip install paho-mqtt                       # 처음 한 번 (2.x)
  python3 push_pose.py 1234                   # 공개 브로커 broker.emqx.io 로 ry 를 0→360 도 돌리며 4초 동안 발행
  python3 push_pose.py 1234 --once '{"ry":80}'   # 메시지 하나만
  python3 push_pose.py 1234 --host xxxx.ala.ap-southeast-1.emqxsl.com --user stu01 --password '****'   # 클라우드(EMQX Serverless, TLS 8883)

구독 쪽: examples/mqtt-pose-twin.html 을 같은 ID·브로커로 연결해 두면 3D 모델이 따라 움직입니다.
메시지 형식: {"x","y","z","rx","ry","rz","t"}  — 빠진 키는 트윈이 이전 값을 유지합니다.
"""
import argparse, json, math, ssl, sys, time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    sys.exit("paho-mqtt 가 없습니다:  pip install paho-mqtt")

p = argparse.ArgumentParser()
p.add_argument("id", help="트윈과 같은 ID (예: 1234)")
p.add_argument("--host", default="broker.emqx.io", help="브로커 주소 (기본: 공개 브로커)")
p.add_argument("--port", type=int, default=None, help="포트 (기본: 공개 1883, 계정 있으면 8883 TLS)")
p.add_argument("--user"); p.add_argument("--password")
p.add_argument("--once", help="이 JSON 하나만 보내고 종료")
p.add_argument("--seconds", type=float, default=4.0, help="자동 회전 시간(초)")
p.add_argument("--hz", type=float, default=5.0, help="초당 발행 횟수 (클라우드 무료 티어는 클라이언트당 10 msg/s 이하)")
a = p.parse_args()

topic = f"khu/pcomp/{a.id}/pose"
cloud = bool(a.user)
port = a.port or (8883 if cloud else 1883)

# paho 2.x 방식 (1.x 는 Client() 첫 인자 없이)
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"pose-py-{a.id}-{int(time.time())%10000}")
except AttributeError:
    client = mqtt.Client(client_id=f"pose-py-{a.id}-{int(time.time())%10000}")
if cloud:
    client.username_pw_set(a.user, a.password)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)      # EMQX Serverless 는 공개 CA → 시스템 인증서로 검증됨
client.connect(a.host, port, keepalive=30)
client.loop_start()
print(f"연결: {a.host}:{port}  토픽: {topic}")

def push(d):
    d["t"] = int(time.time() * 1000)                 # 보낸 시각(ms) — 트윈이 지연 계산에 씀
    s = json.dumps(d)
    client.publish(topic, s)                          # ← push 는 이 한 줄
    print("→", s)

if a.once:
    push(json.loads(a.once))
else:
    t0 = time.time()
    while time.time() - t0 < a.seconds:               # ry 를 한 바퀴, y 를 위아래로
        ph = (time.time() - t0) / a.seconds * 2 * math.pi
        push({"ry": round(math.degrees(ph) % 360 - 180), "y": round(0.5 + 0.5 * math.sin(ph), 2)})
        time.sleep(1 / a.hz)
    push({"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0})   # 원위치

time.sleep(0.5)
client.loop_stop(); client.disconnect()
