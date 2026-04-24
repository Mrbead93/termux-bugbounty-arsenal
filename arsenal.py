#!/usr/bin/env python3
import os, subprocess, datetime, time, sys, threading
from colorama import Fore, init
init(autoreset=True)

last_target = "Unknown"

# ── Dynamic path resolution ─────────────────────────────────
HOME        = os.path.expanduser("~")
PROJECTS    = os.path.join(HOME, "projects")
ARSENAL_DIR = os.path.dirname(os.path.abspath(__file__))

def banner():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║     UNROOTED TERMUX BUG BOUNTY ARSENAL v3.0                  ║
║        ULTIMATE ALL-IN-ONE MOBILE BUG BOUNTY TOOLKIT         ║
╚══════════════════════════════════════════════════════════════╝
    """)

def progress_task(stop_event, message, total_time=60):
    spinner = ['|', '/', '-', '\\']
    bar_length = 25
    i = 0
    start = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start
        progress = min(elapsed / total_time, 1.0)
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        percent = int(progress * 100)
        sys.stdout.write(
            f"\r{Fore.YELLOW}[{spinner[i % 4]}] {message} | {bar} {percent}% "
        )
        sys.stdout.flush()
        time.sleep(0.25)
        i += 1
    sys.stdout.write(
        f"\r{Fore.GREEN}[✓] {message} | {'█' * bar_length} 100% \n"
    )
    sys.stdout.flush()

def run_cmd(cmd, description="", estimated_seconds=60, long_running=False):
    if description:
        print(Fore.MAGENTA + f"[→] {description}")
    print(Fore.YELLOW + f"[+] Running: {cmd}")
    if long_running:
        print(Fore.CYAN + "   ⏳ This may take 5-25 minutes...")

    stop_event = threading.Event()
    thread = threading.Thread(
        target=progress_task,
        args=(stop_event, description, estimated_seconds)
    )
    thread.start()

    try:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True
        )
        stop_event.set()
        thread.join()
        if result.returncode == 0:
            print(Fore.GREEN + "[✓] Completed")
        else:
            print(Fore.RED + f"[!] Finished with errors: {result.stderr[:200]}")
        return result.stdout
    except Exception as e:
        stop_event.set()
        thread.join()
        print(Fore.RED + f"Error: {e}")
        return ""

def run_user_tool(tool_name, display_name):
    """Launch a sibling tool from ~/projects/ dynamically."""
    tool_path = os.path.join(PROJECTS, tool_name, f"{tool_name}.py")
    print(Fore.MAGENTA + f"[→] Launching {display_name}...")

    if os.path.exists(tool_path):
        subprocess.run(
            f"python3 {tool_path}",
            shell=True,
            cwd=os.path.join(PROJECTS, tool_name)
        )
    else:
        print(Fore.RED + f"[✗] Tool not found at: {tool_path}")
        print(Fore.YELLOW + f"[!] Make sure {tool_name} exists in {PROJECTS}/")

def check_tool(tool_name):
    """Check if a system tool is installed."""
    result = subprocess.run(
        f"which {tool_name}",
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0

def full_automated_chain():
    global last_target
    target = input(Fore.WHITE + "Enter target domain (example.com): ").strip()
    if not target:
        print(Fore.RED + "[✗] No target provided.")
        return

    last_target = target
    output_dir = os.path.join(ARSENAL_DIR, "reports", target)
    os.makedirs(output_dir, exist_ok=True)

    wordlist = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")

    print(Fore.CYAN + f"\n🚀 Running ULTIMATE Automated Chain for {target}...")
    print(Fore.DIM + f"   Output directory: {output_dir}\n")

    steps = [
        (f"subfinder -d {target} -o {output_dir}/subdomains.txt",
         "Subdomain Enumeration", 30, False),

        (f"cat {output_dir}/subdomains.txt | httpx -silent "
         f"-o {output_dir}/alive.txt -title -web-server -tech-detect",
         "Live Hosts + Tech Detection", 25, False),

        (f"naabu -list {output_dir}/alive.txt -o {output_dir}/ports.txt",
         "Port Scanning", 40, False),

        (f"gobuster dir -u https://{target} -w {wordlist} "
         f"-o {output_dir}/directories.txt -q",
         "Directory Brute Force", 60, False),

        (f"arjun -u https://{target} -o {output_dir}/parameters.txt",
         "Parameter Discovery", 45, False),

        (f"ffuf -u https://{target}/FUZZ -w {wordlist} "
         f"-o {output_dir}/ffuf.json -mc 200,204,301,302 -q",
         "Advanced Fuzzing", 90, False),

        (f"katana -u https://{target} -o {output_dir}/endpoints.txt",
         "Crawling", 50, False),

        (f"nuclei -l {output_dir}/alive.txt -severity high,critical,medium "
         f"-o {output_dir}/nuclei_results.txt",
         "Nuclei Vulnerability Scan", 300, True),
    ]

    for cmd, desc, est, long in steps:
        tool = cmd.split()[0]
        if not check_tool(tool):
            print(Fore.YELLOW + f"[!] {tool} not installed — skipping {desc}")
            continue
        run_cmd(cmd, desc, est, long)

    print(Fore.GREEN + "\n🎉 ULTIMATE CHAIN COMPLETED!")
    generate_professional_report(target, output_dir)

def generate_professional_report(target=None, output_dir=None):
    global last_target

    if not target:
        target = input(
            Fore.WHITE + f"Target name for report [{last_target}]: "
        ).strip() or last_target

    last_target = target

    if not output_dir:
        output_dir = os.path.join(ARSENAL_DIR, "reports", target)

    os.makedirs(output_dir, exist_ok=True)
    ts  = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    filepath = os.path.join(output_dir, f"bugbounty_report_{ts}.md")

    # ── Gather results ──────────────────────────────────────
    def read_file(name):
        path = os.path.join(output_dir, name)
        if os.path.exists(path):
            with open(path) as f:
                lines = f.readlines()
            return lines, len(lines)
        return [], 0

    subdomains, sub_count   = read_file("subdomains.txt")
    alive, alive_count      = read_file("alive.txt")
    nuclei, vuln_count      = read_file("nuclei_results.txt")
    endpoints, ep_count     = read_file("endpoints.txt")

    # ── Write report ────────────────────────────────────────
    with open(filepath, "w") as f:
        f.write(f"# Bug Bounty Report — {target}\n")
        f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Tool:** Termux Bug Bounty Arsenal v3.0 by Mrbead93\n\n")
        f.write("---\n\n")

        f.write("## Summary\n")
        f.write(f"| Item | Count |\n|---|---|\n")
        f.write(f"| Subdomains Found | {sub_count} |\n")
        f.write(f"| Live Hosts | {alive_count} |\n")
        f.write(f"| Endpoints Discovered | {ep_count} |\n")
        f.write(f"| Vulnerabilities Found | {vuln_count} |\n\n")

        if subdomains:
            f.write("## Subdomains\n```\n")
            f.writelines(subdomains[:50])
            f.write("```\n\n")

        if alive:
            f.write("## Live Hosts\n```\n")
            f.writelines(alive[:50])
            f.write("```\n\n")

        if nuclei:
            f.write("## Vulnerabilities (Nuclei)\n```\n")
            f.writelines(nuclei)
            f.write("```\n\n")

        f.write("---\n*Generated by Termux Bug Bounty Arsenal — for authorised testing only*\n")

    print(Fore.GREEN + f"\n✅ Report saved: {filepath}")

def main_menu():
    global last_target
    while True:
        banner()
        print(Fore.GREEN + f"""  Last Target: {Fore.CYAN}{last_target}
{Fore.GREEN}
  1. Run ReconX              (Manual)
  2. Run CredX               (Manual)
  3. Subdomain + Live Hosts
  4. Port Scanning
  5. Directory Brute Force
  6. Nuclei Scan
  7. Full Automated Chain    (Recommended)
  8. Generate Professional Report
  0. Exit
""")
        choice = input(Fore.WHITE + "Choose → ").strip()

        if choice == "1":
            run_user_tool("reconx", "ReconX")
        elif choice == "2":
            run_user_tool("credx", "CredX")
        elif choice == "3":
            target = input("Target domain: ").strip()
            if target:
                last_target = target
                out = os.path.join(ARSENAL_DIR, "reports", target)
                os.makedirs(out, exist_ok=True)
                run_cmd(
                    f"subfinder -d {target} -o {out}/subdomains.txt",
                    "Subdomain Enumeration", 30
                )
                run_cmd(
                    f"cat {out}/subdomains.txt | httpx -silent "
                    f"-o {out}/alive.txt -title -web-server -tech-detect",
                    "Live Hosts + Tech Detection", 25
                )
        elif choice == "4":
            target = input("Target domain: ").strip()
            if target:
                last_target = target
                out = os.path.join(ARSENAL_DIR, "reports", target)
                os.makedirs(out, exist_ok=True)
                run_cmd(
                    f"naabu -list {out}/alive.txt -o {out}/ports.txt",
                    "Port Scanning", 40
                )
        elif choice == "5":
            target = input("Target domain: ").strip()
            if target:
                last_target = target
                out = os.path.join(ARSENAL_DIR, "reports", target)
                wordlist = os.path.join(ARSENAL_DIR, "wordlists", "directories.txt")
                os.makedirs(out, exist_ok=True)
                run_cmd(
                    f"gobuster dir -u https://{target} -w {wordlist} "
                    f"-o {out}/directories.txt -q",
                    "Directory Brute Force", 60
                )
        elif choice == "6":
            target = input("Target domain: ").strip()
            if target:
                last_target = target
                out = os.path.join(ARSENAL_DIR, "reports", target)
                os.makedirs(out, exist_ok=True)
                run_cmd(
                    f"nuclei -l {out}/alive.txt -severity high,critical,medium "
                    f"-o {out}/nuclei_results.txt",
                    "Nuclei Scan", 300, long_running=True
                )
        elif choice == "7":
            full_automated_chain()
        elif choice == "8":
            generate_professional_report()
        elif choice == "0":
            print(Fore.RED + "\nHappy hunting! 🎯")
            break
        else:
            print(Fore.RED + "[!] Invalid choice")

        input(Fore.DIM + "\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
