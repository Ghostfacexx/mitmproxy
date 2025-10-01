"""
Protocol buffer placeholder files.
These would typically be generated from .proto files using protoc.
For now, we'll create placeholder classes.
"""

from ..utils.logger import Logger

logger = Logger("C2C_PB2")


class NFCData:
    """Placeholder for NFCData protobuf message."""
    
    def __init__(self):
        self.data = b''
    
    def ParseFromString(self, data: bytes) -> None:
        """Parse NFCData from bytes."""
        self.data = data
    
    def SerializeToString(self) -> bytes:
        """Serialize NFCData to bytes."""
        return self.data
    
    def CopyFrom(self, other: 'NFCData') -> None:
        """Copy data from another NFCData instance."""
        self.data = other.data
