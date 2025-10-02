"""
End-to-end test for Wrapper + NFCData processing using real protobufs if available.
"""
from binascii import unhexlify

try:
    from nfcgate_pb2 import NFCData as RealNFCData, Wrapper as RealWrapper
    USING_REAL_PROTO = True
except Exception:
    USING_REAL_PROTO = False
    RealNFCData = None
    RealWrapper = None

if USING_REAL_PROTO:
    NFCData = RealNFCData
    Wrapper = RealWrapper
else:
    from src.protocols.c2c_pb2 import NFCData
    from src.protocols.metaMessage_pb2 import Wrapper

from src.protocols.nfc_handler import process_wrapper_message
from src.core.tlv_parser import parse_tlv, find_tlv, is_valid_tlv


def build_minimal_tlv() -> bytes:
    # Build a minimal valid TLV according to is_valid_tlv heuristic:
    # Outer constructed tag 0x6F with a child 9F37 (AFL) carrying 4 bytes
    # Use a simple inner TLV to avoid constructed-bit confusion in the parser:
    # 6F 06  |  5A 04 11 22 33 44
    return unhexlify("6F065A0411223344")


def make_wrapper_with_nfc(data_bytes: bytes) -> bytes:
    nfc = NFCData()
    # For real proto, set required fields
    if USING_REAL_PROTO:
        nfc.data = data_bytes
        nfc.data_source = NFCData.DataSource.READER
        nfc.data_type = NFCData.DataType.RAW
    else:
        nfc.data = data_bytes

    wrapper = Wrapper()
    # Assign oneof correctly
    if USING_REAL_PROTO:
        wrapper.nfc_data.CopyFrom(nfc)
    else:
        wrapper.NFCData.CopyFrom(nfc)

    return wrapper.SerializeToString()


def test_wrapper_roundtrip_and_signature():
    tlv = build_minimal_tlv()
    wrapper_bytes = make_wrapper_with_nfc(tlv)

    # No private key needed; handler signs internally using provided key; pass None for shim
    state = {
        'bypass_pin': True,
        'block_all': False,
    }

    result = process_wrapper_message(wrapper_bytes, None, state)
    assert result is not None, "Expected processed wrapper result"

    # Parse the result back to extract NFC data
    out_wrapper = Wrapper()
    out_wrapper.ParseFromString(result)

    out_nfc = NFCData()
    if USING_REAL_PROTO:
        out_nfc.CopyFrom(out_wrapper.nfc_data)
    else:
        out_nfc.CopyFrom(out_wrapper.nfc_data if hasattr(out_wrapper, 'nfc_data') else out_wrapper.NFCData)

    out_raw = out_nfc.data
    assert isinstance(out_raw, (bytes, bytearray)) and len(out_raw) > 0
    assert is_valid_tlv(out_raw), "Output should be TLV-like (0x6F/0x77 check is heuristic)"

    tlvs = parse_tlv(out_raw)
    sig = find_tlv(tlvs, 0x9F45)
    assert sig is not None and sig.get('length', 0) > 0, "Signature TLV (0x9F45) should be present"
