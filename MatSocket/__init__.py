import json
import threading
import time
import traceback
import typing
import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Thread
from typing import Callable

import pika
import tqdm
from expiringdict import ExpiringDict

from MatSocket.data_class.ExternalSocket import ExternalSocket
from MatSocket.data_class.MatSocketFunction import MatSocketFunction
from MatSocket.functions.GetSocketInfoFunction import GetSocketInfoFunction
from MatSocket.functions.GetSocketNameFunction import GetSocketNameFunction
from MatSocket.functions.GetSocketNameReplyFunction import GetSocketNameReplyFunction
from MatSocket.functions.PingFunction import PingFunction
from MatSocket.functions.ReplyFunction import ReplyFunction


class MatSocket:

    def __init__(self, self_name: str, host: str, port: int, username: str, password: str, debug: bool = False):
        self.self_name = self_name
        self.__host = host
        self.__port = port
        self.__username = username
        self.__password = password
        self.debug = debug

        self.local_registered_functions: dict[str, MatSocketFunction] = {}

        self.external_sockets: dict[str, ExternalSocket] = {}

        credentials = pika.PlainCredentials('root', 'password')
        self.pika_param = pika.ConnectionParameters(self.__host, self.__port, '/', credentials, heartbeat=0)
        self.send_connection = pika.BlockingConnection(self.pika_param)
        self.send_channel = self.send_connection.channel()

        self.accept_connection = pika.BlockingConnection(self.pika_param)
        self.accept_channel = self.accept_connection.channel()

        self.accept_channel.queue_declare(queue=self.self_name)

        self.accept_channel.basic_consume(queue=self.self_name, on_message_callback=self.callback)

        self.accept_channel.exchange_declare(exchange="broadcast", exchange_type="fanout")
        self.accept_channel.queue_bind(exchange="broadcast", queue=self.self_name)

        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=20)

        self.reply_function = ReplyFunction()
        self.register_function(self.reply_function)
        self.register_function(GetSocketNameFunction())
        self.register_function(GetSocketNameReplyFunction())
        self.register_function(GetSocketInfoFunction())
        self.register_function(PingFunction())

        self.message_queue = Queue()

        def send_message_thread():
            while True:
                try:
                    message = self.message_queue.get()
                    self.send(message["target"], message, exchange=message.get("exchange", ""))
                    self.message_queue.task_done()
                except Exception as e:
                    print(e)

        self.send_message_thread = Thread(target=send_message_thread, daemon=True)
        self.send_message_thread.start()

    def start(self):
        def start_consuming():
            while True:
                try:
                    self.broadcast_message("/system/socket/name", {})
                    self.accept_channel.start_consuming()
                except Exception as e:
                    traceback.print_exc()
                    self.send_connection = pika.BlockingConnection(self.pika_param)
                    self.send_channel = self.send_connection.channel()

                    self.accept_connection = pika.BlockingConnection(self.pika_param)
                    self.accept_channel = self.accept_connection.channel()
                    self.accept_channel.basic_consume(queue=self.self_name, on_message_callback=self.callback)
                    time.sleep(1)

        consuming_thread = Thread(target=start_consuming, daemon=True)
        consuming_thread.start()

    def send(self, routing_key: str, message: dict, exchange: str = ""):
        if self.debug: print("send", message)
        if "exchange" in message:
            del message["exchange"]
        if "target" in message:
            del message["target"]
        message = json.dumps(message, ensure_ascii=False)
        self.send_channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message.encode("utf-8"))

    def callback(self, ch, method, properties, body):
        body = body.decode('utf-8')
        body = json.loads(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if "path" not in body:
            return
        if "origin" not in body:
            return
        if "data" not in body:
            return
        origin = body["origin"]
        data = body["data"]
        reply_id = body.get("replyId", None)
        if origin == self.self_name:
            return
        function = self.local_registered_functions.get(body["path"], None)
        if function is None:
            return
        if self.debug: print("rec", body)

        def task(origin, data, reply_id, function):
            reply = function.handle_message_internal(origin=origin, data=data)
            if reply is not None and len(reply) == 2 and "replyId" in body:
                self.send_reply_message(target=origin, status=reply[0], message=reply[1], reply_id=reply_id)

        self.executor.submit(task, origin, data, reply_id, function)


    def send_reply_message(self, target, status: str, message, reply_id: str):
        self.send_message(target, "/system/reply", {"replyId": reply_id, "data": message, "status": status})

    def register_function(self, function: MatSocketFunction):
        function.main = self
        self.local_registered_functions[function.path] = function

    def broadcast_message(self, path: str, data: dict):
        message = {
            "target": "broadcast",
            "path": path,
            "data": data,
            "origin": self.self_name,
            "exchange": "broadcast"
        }
        self.message_queue.put(message)

    def send_message(self, target: str, path: str, data: dict, reply: bool = False, callback: Callable = None,
                     reply_timeout: int = 1,
                     reply_arguments: typing.Tuple = None) -> dict | None:
        message = {
            "target": target,
            "path": path,
            "data": data,
            "origin": self.self_name,
            "exchange": ""
        }
        if reply or callback is not None:
            reply = True
            reply_id = str(uuid.uuid4())

            if reply_id:
                message["replyId"] = reply_id
                if callback is not None:
                    self.reply_function.reply_callback[reply_id] = callback
                    self.reply_function.reply_arguments[reply_id] = () if reply_arguments is None else reply_arguments
                else:
                    response_event = threading.Event()
                    self.reply_function.reply_lock[reply_id] = response_event

        self.message_queue.put(message)

        if reply and callback is None:
            # Wait for the event to be set or timeout after 1 second
            event_triggered = response_event.wait(reply_timeout)
            reply = None
            if event_triggered:
                # Event was set, response received
                reply = self.reply_function.reply_data.get(reply_id, None)

            # Clean up the reply data
            self.reply_function.clean_reply_data(reply_id)
            return reply


if __name__ == '__main__':
    main = MatSocket("main", "192.168.1.10", 5672, "root", "password", debug=True)

    main.start()

    while True:
        time.sleep(1)
        try:
            print(main.external_sockets.get("MatClock").known_functions)
            # main.external_sockets.get("MatClock").update_functions()
        except Exception as e:
            print(e)
