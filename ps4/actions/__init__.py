import json
from enum import Enum


class Application(Enum):
    NETFLIX = "netflix"
    AMAZON = "amazon"
    DISNEY = "disney"

    def __repr__(self):
        return 'Application.%s' % self


class Command(Enum):
    ON_OFF = "action.devices.commands.OnOff"
    APP_SELECT = "action.devices.commands.appSelect"

    def __repr__(self):
        return 'Command.%s' % self


class Action:
    def __init__(self, command: Command, data: any):
        self.data = data
        self.command = command

    @staticmethod
    def map(raw: bytes):
        data = json.loads(raw, encoding='utf-8')
        command = Command(data['command'])

        if command == Command.ON_OFF:
            return OnOff(command=command, data=data)
        if command == Command.APP_SELECT:
            return AppSelection(command=command, data=data)


class AppSelection(Action):
    def __init__(self, command: Command = None, data: any = None):
        super().__init__(command=command, data=data)
        self.application = None
        if not self.data is None:
            self.application = Application(self.data['params']['newApplication'])

    def get_application(self):
        if self.application == Application.NETFLIX:
            return b'CUSA00129'
        if self.application == Application.AMAZON:
            return b'CUSA00130'
        if self.application == Application.DISNEY:
            return b'CUSA15607'

    def __repr__(self):
        return self.application.__repr__()


class OnOff(Action):
    def __init__(self, command: Command = None, data: any = None):
        super().__init__(command=command, data=data)
        self.state = None
        if not self.data is None:
            self.state = self.data['params']['on']

    def __repr__(self):
        return "Action.<%s>" % "ON" if not self.state else "OFF"
