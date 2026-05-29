import paramiko


class SessionManager:

    def __init__(self):
        self.sessions = {}

    def connect(self, name, host, username, password):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=host, username=username, password=password)

        self.sessions[name] = client
        return True

    def run_command(self, name, command):
        client = self.sessions.get(name)
        if not client:
            return "No session"

        stdin, stdout, stderr = client.exec_command(command)
        return stdout.read().decode()

    def disconnect(self, name):
        if name in self.sessions:
            self.sessions[name].close()
            del self.sessions[name]