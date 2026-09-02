from app.services.mapping import _universe_rows, resolve
by_id, by_primary = _universe_rows()
print("by_id size:", len(by_id))
print("CA keys sample:", [k for k in list(by_id)[:3]] if by_id else "EMPTY")
print("CA:RY:TSX in by_id:", "CA:RY:TSX" in by_id)
print("RY in by_primary:", "RY" in by_primary)
import itertools
print("sample CA entries:", dict(itertools.islice((k, v) for k, v in by_id.items() if k.startswith('CA:')), 0, 3))
r = resolve("RY.TO")
print("resolve RY.TO:", r)
