from polymath.app import Application
from polymath.launcher.app import SimpleLauncher

class ServerListener(SimpleLauncher):

    @property
    def host(self)->str:
        return self.__host

    @property
    def port(self)->int:
        return self.__port

    def __init__(self, app: Application, host: str, port: int):
        super(ServerListener, self).__init__(app=app)
        self.__host = host
        self.__port = port



