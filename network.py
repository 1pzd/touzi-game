import socket
import json
import threading

class Network:
    def __init__(self, server_ip, port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.port = port
        self.addr = (self.server_ip, self.port)
        self.connected = False
        self.player_id = None  # 1: 房主, 2: 加入者
        self.room_code = None
        self.msg_queue = []  # 接收到的消息队列
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.connected = True
            # 启动接收线程
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Connection Error: {e}")
            return False

    def receive_loop(self):
        while self.connected:
            try:
                msg = self.client.recv(4096).decode()
                if not msg:
                    break
                data = json.loads(msg)
                with self.lock:
                    self.msg_queue.append(data)
            except Exception as e:
                print(f"Receive Error: {e}")
                self.connected = False
                break

    def send(self, data):
        """发送数据给服务器"""
        try:
            self.client.send(json.dumps(data).encode())
        except socket.error as e:
            print(f"Send Error: {e}")

    def get_msg(self):
        """获取一条最新消息"""
        with self.lock:
            if self.msg_queue:
                return self.msg_queue.pop(0)
        return None

    def create_room(self):
        self.send({"action": "CREATE"})

    def join_room(self, code):
        self.send({"action": "JOIN", "code": code})

    def send_game_action(self, action_type, payload):
        """发送游戏操作"""
        self.send({
            "action": "GAME_DATA",
            "type": action_type,
            "payload": payload
        })
