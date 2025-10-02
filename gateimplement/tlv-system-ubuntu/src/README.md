Protobufs and NFC Wrapper Handling

Overview
- This package prefers the real generated protobufs from `nfcgate.proto` if they are importable as `nfcgate_pb2`.
- If not available, it falls back to lightweight shims in `protocols/c2c_pb2.py` and `protocols/metaMessage_pb2.py` that mimic the field names and oneof structure used in the real messages.

Real vs Shim
- Real messages (from `nfcgate_pb2`) require setting required fields in `NFCData`: `data`, `data_source`, and `data_type`.
- The shim only serializes the `data` bytes and ignores other fields, but keeps attributes so code compiles.
- `protocols/nfc_handler.py` detects the real module and adapts field access accordingly.

Tests
- A minimal test exists at `tests/test_nfc_wrapper_flow.py` that builds a Wrapper with NFCData, runs it through `process_wrapper_message`, and verifies the resulting TLV contains a signature tag (0x9F45).

Generating Real Protobufs
1. Ensure `protoc` is installed.
2. Generate Python code from the root `nfcgate.proto`:
   - Place the generated module where Python can import it as `nfcgate_pb2`.
3. Re-run tests to exercise the real messages.
