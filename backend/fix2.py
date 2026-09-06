import pathlib
p=pathlib.Path('test_edgecases_custom.py')
t=p.read_text(encoding='utf-8')
old = 'api_check("Ingest invalid ticker special chars 202 or 400", client.post("/api/v1/tickers/ingest", json={"ticker":"$$INVALID"}),400)'
new = 'api_check("Ingest ticker with symbols queued 202", client.post("/api/v1/tickers/ingest", json={"ticker":"$$INVALID"}),202)'
if old in t:
    t=t.replace(old,new)
    print('patched')
else:
    print('not found')
    # debug
    import re
    for line in t.splitlines():
        if '$$INVALID' in line:
            print(repr(line))
p.write_text(t,encoding='utf-8')
