import paramiko

class SSHClient:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password
        )

    def run_command(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return stdout.read().decode()

    def close(self):
        self.client.close()