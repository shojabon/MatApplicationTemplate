from expiringdict import ExpiringDict

from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class ReplyFunction(MatSocketFunction):

    def information(self):
        self.path = "/system/reply"
        self.function_schema = None

    def __init__(self):
        super().__init__()
        self.reply_data = ExpiringDict(1000000, 5)
        self.reply_lock = ExpiringDict(1000000, 5)
        self.reply_callback = ExpiringDict(1000000, 5)
        self.reply_arguments = ExpiringDict(1000000, 5)

    def clean_reply_data(self, reply_id: str):
        if reply_id in self.reply_data: del self.reply_data[reply_id]
        if reply_id in self.reply_lock: del self.reply_lock[reply_id]
        if reply_id in self.reply_callback: del self.reply_callback[reply_id]
        if reply_id in self.reply_arguments: del self.reply_arguments[reply_id]

    def handle_message(self, origin: str, data: dict):
        response_id = data.get("replyId") if "replyId" in data else None
        if response_id is None:
            return
        del data["replyId"]
        if response_id in self.reply_callback:
            self.reply_callback.get(response_id)(data, *self.reply_arguments.get(response_id))
            # Store the response
        if response_id in self.reply_lock:
            self.reply_data[response_id] = data
            # Trigger the event to unblock the waiting thread
            self.reply_lock[response_id].set()
