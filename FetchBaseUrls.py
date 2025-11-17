import os
import ssl
import time
from urllib.parse import urlparse, unquote
from urllib.request import urlopen, Request

Request_Link1 = "https://webproxy.911proxy.com/request?p=GgkeGkY8OV0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="
Request_Link2 = "https://webproxy.911proxy.com/request?p=GgkeGkY4Ol0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="
Request_Link3 = "https://webproxy.911proxy.com/request?p=GgkeGkYuKF0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="
Request_Link4 = "https://webproxy.911proxy.com/request?p=GgkeGkY1IV0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="
Request_Link5 = "https://webproxy.911proxy.com/request?p=GgkeGkY6Ll0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="
Request_Link6 = "https://webproxy.911proxy.com/request?p=GgkeGkYyNV0ORhMPDwsIQVRUFxINHgsOCBNVEhRUExcICxcaAh4JVBIVHx4DVRMPFhc="

Test1 = "https://vs-hls-pushb-uk-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_alba/t=3840/v=pv14/b=5070016/main.m3u8"
Test2 = "https://amagi-streams.akamaized.net/hls/live/2113391/cbcheartland/master.m3u8"
Test3 = "https://d2i0inzobjlgvu.cloudfront.net/History_3651080.m3u8"
Test4 = "https://fv23-three.fullscreen.nz/index_18.m3u8"
Test5 = "https://9now-livestreams-fhd-t.akamaized.net/u/prod/simulcast/syd/life/hls/r1/index.m3u8"
Test6 = "https://amg01448-amg01448c15-samsung-in-3494.playouts.now.amagi.tv/playlist/amg01448-samsungindia-historychannelenglish-samsungin/playlist.m3u8"

_SSL_CTX = ssl._create_unverified_context()


def _resolve_base(request_link: str, timeout: int = 20, attempts: int = 3, pause_sec: float = 2.0) -> str:
    for i in range(attempts):
        print(f"[DEBUG] Resolving base for `{request_link}`  (attempt {i+1}/{attempts})")
        try:
            new_url = request_link.replace("/request?p=", "/new?p=")
            req = Request(
                new_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "text/plain,*/*;q=0.8",
                    "Referer": "https://webproxy.911proxy.com/request",
                },
            )
            with urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                text = resp.read(256 * 1024).decode("utf-8", errors="ignore").strip()
            print(f"[DEBUG] new() -> `{text[:100]}` ")

            if text.startswith("http://") or text.startswith("https://"):
                req2 = Request(
                    text,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept": "text/html,*/*;q=0.8",
                        "Referer": "https://webproxy.911proxy.com/request",
                    },
                )
                with urlopen(req2, timeout=timeout, context=_SSL_CTX) as resp2:
                    final2 = resp2.geturl()
                print(f"[DEBUG] iprequest final_url -> `{final2}` ")

                parsed = urlparse(final2)
                segs = [s for s in parsed.path.split("/") if s]
                if segs:
                    secret = segs[0]
                    return f"{parsed.scheme}://{parsed.netloc}/{secret}/"
        except Exception as e:
            print(f"[DEBUG] resolve error: {e}")
        time.sleep(pause_sec)
    raise RuntimeError("Failed to resolve base URL")


def _endpoint_status(test_url: str, timeout: int = 8) -> int:
    req = Request(test_url, headers={"User-Agent": "curl/8.0"})
    try:
        with urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return getattr(resp, "status", resp.getcode())
    except Exception as e:
        print(f"[DEBUG] status error for {test_url}: {e}")
        return 0


def _resolve_with_test(request_link: str, test_link: str, max_attempts: int = 3) -> str:
    last_base = ""
    for i in range(max_attempts):
        try:
            base = _resolve_base(request_link)
        except Exception as e:
            print(f"[DEBUG] resolve_base failed: {e}")
            time.sleep(0.6)
            continue
        last_base = base
        combined = f"{base}{test_link}"
        print(f"[DEBUG] Test attempt {i+1}/{max_attempts} -> `{combined}` ")
        status = _endpoint_status(combined)
        print(f"[DEBUG] HTTP status -> {status}")
        if status == 200:
            print("[DEBUG] Test OK; using base")
            return base
        print("[DEBUG] Test failed; re-resolving base")
        time.sleep(0.6)
    if last_base:
        print("[DEBUG] Max test attempts reached; using last base")
        return last_base
    print("[DEBUG] Max test attempts reached; no base resolved")
    return ""


def main():
    pairs = [
        (Request_Link1, Test1),
        (Request_Link2, Test2),
        (Request_Link3, Test3),
        (Request_Link4, Test4),
        (Request_Link5, Test5),
        (Request_Link6, Test6),
    ]
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "BaseURLs.txt")
    backup_path = os.path.join(here, "BaseURLsbk.txt")

    prev_lines = []
    backup_lines = []
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as pf:
                prev_lines = [ln.rstrip("\n") for ln in pf.readlines()]
            with open(backup_path, "w", encoding="utf-8") as bk:
                bk.write("\n".join(prev_lines) + ("\n" if prev_lines else ""))
            print("[DEBUG] Previous BaseURLs.txt read and backup written")
        except Exception as e:
            print(f"[DEBUG] prev read/backup error: {e}")
    elif os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as bf:
                backup_lines = [ln.rstrip("\n") for ln in bf.readlines()]
            print("[DEBUG] Backup BaseURLsbk.txt read")
        except Exception as e:
            print(f"[DEBUG] backup read error: {e}")

    results = []
    for idx, (rl, tl) in enumerate(pairs, start=1):
        print(f"[DEBUG] === Processing Request_Link{idx} with Test{idx} ===")
        base = _resolve_with_test(rl, tl)
        results.append(base)
        time.sleep(0.5)

    for i in range(len(results)):
        if not results[i]:
            prev_val = prev_lines[i] if i < len(prev_lines) else ""
            bk_val = backup_lines[i] if i < len(backup_lines) else ""
            if prev_val:
                print(f"[DEBUG] Fallback to previous line {i+1}")
                results[i] = prev_val
            elif bk_val:
                print(f"[DEBUG] Fallback to backup line {i+1}")
                results[i] = bk_val
            else:
                print(f"[DEBUG] No previous/backup value for line {i+1}; keeping empty")

    with open(out_path, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line + "\n")


if __name__ == "__main__":
    main()