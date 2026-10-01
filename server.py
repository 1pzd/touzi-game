import socket
import threading
import json
import random
import string

# 配置
SERVER_IP = "0.0.0.0"  # 监听所有网卡
PORT = 5555
BUFFER_SIZE = 4096

# 存储房间信息: { "room_code": [conn1, conn2] }
rooms = {}
# 存储连接对应的房间: { conn: "room_code" }
conn_room_map = {}

def generate_room_code():
    """生成4位随机房间号"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if code not in rooms:
            return code

def broadcast_to_room(room_code, sender_conn, data):
    """将数据转发给房间内的其他人"""
    if room_code in rooms:
        for conn in rooms[room_code]:
            if conn != sender_conn:
                try:
                    conn.send(json.dumps(data).encode())
                except:
                    pass

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    current_room = None
    
    try:
        while True:
            msg = conn.recv(BUFFER_SIZE)
            if not msg:
                break
            
            try:
                data = json.loads(msg.decode())
            except json.JSONDecodeError:
                continue

            action = data.get("action")

            if action == "CREATE":
                room_code = generate_room_code()
                rooms[room_code] = [conn]
                conn_room_map[conn] = room_code
                current_room = room_code
                print(f"[ROOM CREATED] {addr} created room {room_code}")
                conn.send(json.dumps({"action": "ROOM_CREATED", "code": room_code, "player_id": 1}).encode())

            elif action == "JOIN":
                code = data.get("code")
                if code in rooms and len(rooms[code]) < 2:
                    rooms[code].append(conn)
                    conn_room_map[conn] = code
                    current_room = code
                    print(f"[ROOM JOINED] {addr} joined room {code}")
                    # 通知加入者你是P2
                    conn.send(json.dumps({"action": "JOIN_SUCCESS", "player_id": 2}).encode())
                    # 通知房主(P1)有人进来了
                    broadcast_to_room(code, conn, {"action": "PLAYER_JOINED"})
                else:
                    conn.send(json.dumps({"action": "ERROR", "msg": "房间不存在或已满"}).encode())

            elif action == "GAME_DATA":
                # 核心功能：转发游戏操作（如投骰子结果、技能使用等）
                if current_room:
                    broadcast_to_room(current_room, conn, data)

    except Exception as e:
        print(f"[EXCEPTION] {addr}: {e}")
    finally:
        print(f"[DISCONNECT] {addr} disconnected.")
        if current_room and current_room in rooms:
            if conn in rooms[current_room]:
                rooms[current_room].remove(conn)
            if not rooms[current_room]:
                del rooms[current_room]
                print(f"[ROOM CLOSED] Room {current_room} deleted.")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER_IP}:{PORT}")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
