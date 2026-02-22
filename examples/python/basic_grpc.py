"""Example: Capture gRPC calls with Smello.

Calls the public grpcb.in test service (like httpbin for gRPC) and captures
all traffic. Captured calls appear at http://localhost:5110 alongside HTTP
traffic.

Usage:
    uv run python examples/python/basic_grpc.py

Prerequisites:
    uv pip install grpcio protobuf
    # (proto codegen already done — grpcbin_pb2*.py are checked in)
"""

import sys
from pathlib import Path

# Add examples/python to path so grpcbin_pb2 imports work from repo root
sys.path.insert(0, str(Path(__file__).parent))

import smello

smello.init(server_url="http://localhost:5110")

import grpc  # noqa: E402
import grpcbin_pb2  # noqa: E402
import grpcbin_pb2_grpc  # noqa: E402

GRPCBIN_HOST = "grpcb.in:9000"


def main():
    # 1) Successful unary calls
    with grpc.insecure_channel(GRPCBIN_HOST) as channel:
        stub = grpcbin_pb2_grpc.GRPCBinStub(channel)

        # Echo a DummyMessage back
        resp = stub.DummyUnary(
            grpcbin_pb2.DummyMessage(f_string="hello from smello", f_int32=42)
        )
        print(f"DummyUnary → f_string={resp.f_string!r}, f_int32={resp.f_int32}")

        # Get service index
        idx = stub.Index(grpcbin_pb2.EmptyMessage())
        print(f"Index      → {idx.description!r} ({len(idx.endpoints)} endpoints)")

        # Empty no-op call
        stub.Empty(grpcbin_pb2.EmptyMessage())
        print("Empty      → OK")

    # 2) Trigger a gRPC error (NOT_FOUND = 5)
    print("\nTriggering gRPC NOT_FOUND error...")
    try:
        with grpc.insecure_channel(GRPCBIN_HOST) as channel:
            stub = grpcbin_pb2_grpc.GRPCBinStub(channel)
            stub.SpecificError(
                grpcbin_pb2.SpecificErrorRequest(code=5, reason="testing smello")
            )
    except grpc.RpcError as e:
        print(f"Got expected error: {e.code().name} — {e.details()}")

    # Flush captures before exiting
    smello.flush(timeout=3)
    print("\nDone. Open http://localhost:5110 to see captured gRPC calls.")


if __name__ == "__main__":
    main()
