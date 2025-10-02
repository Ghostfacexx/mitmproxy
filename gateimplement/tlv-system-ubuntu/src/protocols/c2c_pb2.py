"""
Protocol buffer placeholders aligned to nfcgate.proto (proto2).

These are lightweight shims that expose the same field names as the real
generated code (nfcgate_pb2). They do NOT perform real protobuf
serialization; instead, they treat the content as opaque bytes for
in-repo processing flows.

If you need real protobuf interoperability, switch imports to use the
generated module (nfcgate_pb2) and set all required fields accordingly.
"""

from typing import Optional
from ..utils.logger import Logger

logger = Logger("C2C_PB2")


class NFCData:
    """Placeholder for NFCData protobuf message.

    Fields (matching nfcgate.proto):
      - data: bytes (required in real proto)
      - data_source: enum { READER=1, CARD=2 } (required in real proto)
      - data_type: enum { INITIAL=1, RAW=2 } (required in real proto)
      - timestamp: int (optional)

    This shim only carries 'data' for internal processing. Other fields are
    present to keep the API surface compatible but are not serialized.
    """

    class DataSource:
        READER = 1
        CARD = 2

    class DataType:
        INITIAL = 1
        RAW = 2

    def __init__(self):
        self.data: bytes = b""
        self.data_source: int = NFCData.DataSource.READER
        self.data_type: int = NFCData.DataType.RAW
        self.timestamp: Optional[int] = None

    def ParseFromString(self, data: bytes) -> None:
        """Shim parse: treat incoming bytes as raw NFC payload."""
        self.data = data

    def SerializeToString(self) -> bytes:
        """Shim serialize: return raw NFC payload bytes only."""
        return self.data

    def CopyFrom(self, other: 'NFCData') -> None:
        """Copy fields from another NFCData instance."""
        self.data = getattr(other, 'data', b"")
        self.data_source = getattr(other, 'data_source', NFCData.DataSource.READER)
        self.data_type = getattr(other, 'data_type', NFCData.DataType.RAW)
        self.timestamp = getattr(other, 'timestamp', None)
