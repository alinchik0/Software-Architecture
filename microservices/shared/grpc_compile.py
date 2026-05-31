# shared/grpc_compile.py
from pathlib import Path
from grpc_tools import protoc

def compile_protos() -> None:
    root = Path(__file__).resolve().parents[1]
    proto = root / "proto"
    if not proto.exists():
        return
    protoc.main(["grpc_tools.protoc", f"-I{proto}", f"--python_out={root}", f"--grpc_python_out={root}", str(proto / "user.proto"), str(proto / "playlist.proto")])
