#!/usr/bin/env python3
import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


NETCRAFT_URL = "https://searchdns.netcraft.com/?host=.{domain}"


def normalize_host(host: str) -> str:
    host = (host or "").strip().lower().rstrip(".")
    host = re.sub(r"\s+", "", host)
    return host


def jitter_sleep(base: float, jitter: float) -> None:
    if base <= 0:
        return
    time.sleep(base + (random.random() * max(0.0, jitter)))


def accept_cookies(driver, timeout: int = 3) -> bool:
    selectors = [
        (By.XPATH, "//button[contains(@class, 'btn-info') and contains(@class, 'teal')]"),
        (By.XPATH, "//button[contains(., 'Accept')]"),
        (By.XPATH, "//button[contains(., 'I Agree')]"),
        (By.XPATH, "//button[contains(., 'Agree')]"),
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            return True
        except Exception:
            pass
    return False


def wait_for_results_or_page(driver, timeout: int) -> None:
    # Wait for either results rows OR any page body to be present
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    # Then try to wait for at least 1 results row (not always present)
    try:
        WebDriverWait(driver, min(timeout, 15)).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".results-table tbody tr"))
        )
    except TimeoutException:
        pass


def extract_hosts(driver) -> list[str]:
    hosts: list[str] = []
    rows = driver.find_elements(By.CSS_SELECTOR, ".results-table tbody tr")
    for row in rows:
        tds = row.find_elements(By.CSS_SELECTOR, "td")
        # Netcraft results: column 2 is usually host
        if len(tds) >= 2:
            hosts.append(tds[1].text.strip())
    return hosts


def find_next_url(driver) -> str | None:
    candidates = [
        (By.CSS_SELECTOR, "a[rel='next']"),
        (By.XPATH, "//a[contains(.,'Next') and contains(@href,'host=')]"),
        (By.CSS_SELECTOR, ".pagination a[href*='host='][href*='position=']"),
        (By.CSS_SELECTOR, "a.btn-info[href*='host='][href*='position=']"),
    ]
    for by, sel in candidates:
        try:
            el = driver.find_element(by, sel)
            href = el.get_attribute("href")
            if href:
                return href
        except NoSuchElementException:
            continue
    return None


def emit(host: str, fmt: str) -> None:
    if fmt == "jsonl":
        print(json.dumps({"subdomain": host, "source": "netcraft"}, ensure_ascii=False))
    else:
        print(host)


def netcraft_enum(
    domain: str,
    out_path: Path,
    headless: bool,
    max_pages: int,
    delay: float,
    jitter: float,
    timeout: int,
    user_agent: str | None,
    resume: bool,
    fmt: str,
) -> int:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")

    seen: set[str] = set()
    if resume and out_path.exists():
        for line in out_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            h = normalize_host(line)
            if h:
                seen.add(h)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    def add_and_persist(hosts: list[str]) -> int:
        new_count = 0
        with out_path.open("a", encoding="utf-8") as f:
            for raw in hosts:
                h = normalize_host(raw)
                if not h:
                    continue

                # Keep only names under the target domain (no DNS resolution here)
                if not (h == domain or h.endswith("." + domain)):
                    continue

                if h in seen:
                    continue

                seen.add(h)
                f.write(h + "\n")
                emit(h, fmt)
                new_count += 1
        return new_count

    driver = None
    total_new = 0

    try:
        driver = webdriver.Chrome(options=options)
        url = NETCRAFT_URL.format(domain=domain)
        driver.get(url)

        accept_cookies(driver)
        wait_for_results_or_page(driver, timeout=timeout)

        title = (driver.title or "").lower()
        if "attention required" in title or "cloudflare" in title:
            raise RuntimeError("Blocked by an anti-bot page (Cloudflare/verification). Run non-headless and solve once, or try a different network/profile.")

        page = 0
        while True:
            page += 1
            wait_for_results_or_page(driver, timeout=timeout)

            hosts = extract_hosts(driver)
            total_new += add_and_persist(hosts)

            if max_pages and page >= max_pages:
                break

            next_url = find_next_url(driver)
            if not next_url:
                break

            jitter_sleep(delay, jitter)
            driver.get(next_url)
            accept_cookies(driver)

        return total_new

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Enumerate subdomains from Netcraft SearchDNS using Selenium.")
    ap.add_argument("domain", help="Target domain (example.com)")
    ap.add_argument("-o", "--output", default="subdomains.netcraft", help="Output file path")
    ap.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    ap.add_argument("--max-pages", type=int, default=0, help="Stop after N pages (0 = all)")
    ap.add_argument("--delay", type=float, default=1.0, help="Base delay between pages (seconds)")
    ap.add_argument("--jitter", type=float, default=1.0, help="Random jitter added to delay (seconds)")
    ap.add_argument("--timeout", type=int, default=25, help="Wait timeout for page/results (seconds)")
    ap.add_argument("--user-agent", default=None, help="Custom User-Agent string")
    ap.add_argument("--resume", action="store_true", help="Dedup against existing output file and continue")
    ap.add_argument("--format", choices=["text", "jsonl"], default="text", help="Stdout output format")
    args = ap.parse_args()

    domain = normalize_host(args.domain)
    if not domain or "." not in domain:
        print("Invalid domain.", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.output)

    try:
        new_count = netcraft_enum(
            domain=domain,
            out_path=out_path,
            headless=args.headless,
            max_pages=args.max_pages,
            delay=args.delay,
            jitter=args.jitter,
            timeout=args.timeout,
            user_agent=args.user_agent,
            resume=args.resume,
            fmt=args.format,
        )
        # Exit code 0 even if 0 results; orchestrator can decide what that means.
        sys.exit(0)
    except Exception as e:
        print(f"[netcraft] error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
