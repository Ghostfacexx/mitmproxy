"""
MetaMessage placeholder aligned to nfcgate.proto Wrapper oneof names.

Fields (in real proto oneof 'message'):
  - session: Session
  - data: Data { blob: bytes }
  - anticol: Anticol { uid/atqa/sak/historical }
  - nfc_data: NFCData
  - status: Status

This shim keeps a single active field and only serializes raw NFCData
bytes if nfc_data is the active field.
"""

from .c2c_pb2 import NFCData
from ..utils.logger import Logger

logger = Logger("MetaMessage_PB2")


class Anticol:
    def __init__(self):
        self.uid = b''
        self.atqa = b''
        self.sak = b''
        self.historical = b''


class Status:
    def __init__(self):
        # In real proto this is an enum + optional message
        self.type = 0
        self.message = ''


class Data:
    def __init__(self):
        # In real proto: optional bytes blob = 2
        self.blob = b''


class Session:
    def __init__(self):
        # In real proto: required opcode + optional errcode/session_secret
        self.opcode = 0
        self.errcode = 0
        self.session_secret = ''


class Wrapper:
    def __init__(self):
        self.session = Session()
        self.data = Data()
        self.anticol = Anticol()
        self.nfc_data = NFCData()
        self.status = Status()
        self._which_field = None  # one of: 'session','data','anticol','nfc_data','status'

    def ParseFromString(self, data: bytes) -> None:
        """Shim parse: assume payload is NFCData if non-empty."""
        if data:
            self.nfc_data.ParseFromString(data)
            self._which_field = 'nfc_data'

    def SerializeToString(self) -> bytes:
        if self._which_field == 'nfc_data':
            return self.nfc_data.SerializeToString()
        elif self._which_field == 'data':
            # For shim purposes, return inner blob as top-level bytes if present
            return self.data.blob or b''
        return b''

    def HasField(self, field_name: str) -> bool:
        # Accept both snake_case and PascalCase for compatibility
        if not self._which_field:
            return False
        if field_name == self._which_field:
            return True
        if field_name.lower() == self._which_field:
            return True
        # Legacy alias: 'NFCData' considered set if nfc_data contains bytes
        if field_name == 'NFCData' and getattr(self.nfc_data, 'data', b''):
            return True
        return False

    def WhichOneof(self, oneof_name: str) -> str:
        return self._which_field or ''

    # Convenience CopyFrom methods to mimic generated API
    class _FieldProxy:
        def __init__(self, parent, field_name):
            object.__setattr__(self, '_parent', parent)
            object.__setattr__(self, '_field_name', field_name)

        def _target(self):
            return getattr(self._parent, self._field_name)

        def CopyFrom(self, other):
            # If target object has CopyFrom, forward; otherwise assign
            target = self._target()
            if hasattr(target, 'CopyFrom'):
                target.CopyFrom(other)
            else:
                setattr(self._parent, self._field_name, other)
            self._parent._which_field = self._field_name

        def __getattr__(self, name):
            # Back-compat alias: Data.payload -> Data.blob
            if name == 'payload' and self._field_name == 'data':
                return getattr(self._target(), 'blob', b'')
            return getattr(self._target(), name)

        def __setattr__(self, name, value):
            if name in ('_parent', '_field_name'):
                object.__setattr__(self, name, value)
            elif name == 'payload' and self._field_name == 'data':
                setattr(self._target(), 'blob', value)
                self._parent._which_field = self._field_name
            else:
                setattr(self._target(), name, value)
                self._parent._which_field = self._field_name

    @property
    def NFCData(self):
        # Backward-compat alias for older code, returns a proxy
        return self._FieldProxy(self, 'nfc_data')

    @property
    def Data(self):
        return self._FieldProxy(self, 'data')

    @property
    def Anticol(self):
        return self._FieldProxy(self, 'anticol')

    @property
    def Session(self):
        return self._FieldProxy(self, 'session')

    @property
    def Status(self):
        return self._FieldProxy(self, 'status')
