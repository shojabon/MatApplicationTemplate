from expiringdict import ExpiringDict

from MatSocket.data_class.MatSocketFunction import MatSocketFunction


class GetSocketInfoFunction(MatSocketFunction):

    def information(self):
        self.path = "/system/socket/info"
        self.function_schema = None
    def handle_message(self, origin: str, data: dict):
        result = {
            "name": self.main.self_name
        }
        functions = {}
        for key, value in self.main.local_registered_functions.items():
            functions[value.path] = value.get_json()
        result["functions"] = functions
        return "success", result
