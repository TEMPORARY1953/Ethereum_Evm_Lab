"""Checks the running loopback UI. No reserve, signature or transaction send."""
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

ORIGIN = "http://127.0.0.1:8765"
ROOT = Path(__file__).resolve().parents[2]
opener = build_opener(ProxyHandler({}))


def request(path, payload=None, origin=None, host=None):
    headers = {}
    if origin:
        headers["Origin"] = origin
    if host:
        headers["Host"] = host
    if payload is not None:
        headers["Content-Type"] = "application/json"
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(ORIGIN + path, data=data, headers=headers)
    try:
        response = opener.open(req, timeout=60)
    except HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers), response.read()


def main():
    status, headers, html = request("/")
    assert status == 200 and b"Vmk Rulit Token" in html
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "connect-src 'self'" in headers["Content-Security-Policy"]
    assert "form-action 'none'" in headers["Content-Security-Policy"]
    assert not any(k.lower().startswith("access-control-allow") for k in headers)
    assert b'type="password"' not in html and b"<form" not in html
    assert request("/api/plan", host="evil.example")[0] == 403
    for origin in (None, "https://evil.example", "null"):
        assert request("/api/reserve", {"step": "deploy"}, origin=origin)[0] == 403
    assert request("/../.env")[0] == 404
    assert request("/api/rpc", {"method": "eth_sendTransaction"}, origin=ORIGIN)[0] == 404
    assert request("/api/record", {"step": "deploy", "hash": "invalid"}, origin=ORIGIN)[0] == 400
    script_status, _, script = request("/signer.js")
    assert script_status == 200
    text = script.decode()
    assert text.count('method: "eth_sendTransaction"') == 1
    for prohibited in ("personal_sign", 'method: "eth_sign"', "eth_signTypedData", "wallet_grantPermissions",
                       "wallet_requestPermissions", "sendBeacon", "XMLHttpRequest", "https://"):
        assert prohibited not in text, prohibited
    _, _, body = request("/api/plan")
    plan = json.loads(body)
    assert plan["name"] == "Vmk Rulit Token" and plan["symbol"] == "VMKRULIT"
    assert plan["approved"] is True
    initial_transactions = plan["state"]["transactions"]
    preview_result = {"status": "SKIPPED: operation already reserved/sent by user"}
    if not initial_transactions:
        assert request("/api/reserve", {"step": "deploy", "planId": "stale-plan"}, origin=ORIGIN)[0] == 400
        status, _, body = request("/api/preview", {"step": "deploy", "planId": plan["planId"]}, origin=ORIGIN)
        assert status == 200, body.decode()
        review = json.loads(body)
        assert review["transaction"]["value"] == "0x0"
        assert review["transaction"]["data"] == plan["creationData"]
        assert review["decoded"]["chainId"] == 11155111
        assert int(review["estimatedFeeWei"]) > 0
        preview_result = {k: review[k] for k in ("gasEstimate", "estimatedFeeWei", "maximumFeeWei", "estimatedAtBlock", "decoded")}
    _, _, after = request("/api/plan")
    assert json.loads(after)["state"]["transactions"] == initial_transactions
    result = {"status": "PASS", "origin": ORIGIN,
              "checks": ["Host", "Origin/CSRF", "CSP", "no CORS", "no secret file routes",
                         "no password forms", "no third-party scripts", "one explicit wallet send path",
                         "no approve/sign/permission methods", "read-only preview does not reserve/send"],
              "deploymentPreview": preview_result}
    (ROOT / "checks/task4_http_security.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
