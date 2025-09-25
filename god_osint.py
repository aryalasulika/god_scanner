

import sys
import re
import argparse
import random
try:
    import asyncio
    import aiohttp
except ImportError:
    print("[!] Modul aiohttp belum terinstall. Install dengan: pip install aiohttp")
    sys.exit(1)
try:
    import pyfiglet
except ImportError:
    print("[!] Modul pyfiglet belum terinstall. Install dengan: pip install pyfiglet")
    sys.exit(1)
try:
    from colorama import init, Fore, Back, Style
except ImportError:
    print("[!] Modul colorama belum terinstall. Install dengan: pip install colorama")
    sys.exit(1)
try:
    from tqdm import tqdm
except ImportError:
    print("[!] Modul tqdm belum terinstall. Install dengan: pip install tqdm")
    sys.exit(1)

# Inisialisasi Colorama
init(autoreset=True)

def display_banner():
    """Menampilkan banner program dan info versi dengan warna random."""
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    color = random.choice(colors)
    ascii_banner = pyfiglet.figlet_format("USER CHECKER")
    print(color + ascii_banner)
    print(color + "=" * 60)
    print(color + "        Simple OSINT Username Checker by ReinsV")
    print(color + f"        Versi Tools : 1.2 | Python : {sys.version.split()[0]}")
    print(color + "        Dependensi  : aiohttp, pyfiglet, colorama, tqdm")
    print(color + "=" * 60)
    print(color + "\n")


# Daftar situs default
DEFAULT_SITES = {
    "Instagram": "https://www.instagram.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Facebook": "https://www.facebook.com/{}",
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "YouTube": "https://www.youtube.com/user/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Vimeo": "https://vimeo.com/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Medium": "https://medium.com/@{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Flickr": "https://www.flickr.com/people/{}",
    "About.me": "https://about.me/{}",
    "GitLab": "https://gitlab.com/{}",
}

def load_sites_from_file(file_path):
    sites = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip() and ':' in line:
                    name, url = line.strip().split(':', 1)
                    sites[name.strip()] = url.strip()
    except Exception as e:
        print(Fore.YELLOW + f"[!] Gagal memuat custom sites: {e}")
    return sites if sites else DEFAULT_SITES

async def check_username(session, site, url_template, username, retry=2, timeout=10, proxy=None, log_error=None, detail=False):
    """
    Fungsi async untuk memeriksa satu username di satu situs, dengan retry, proxy, dan log error.
    """
    url = url_template.format(username)
    for attempt in range(retry+1):
        try:
            req_kwargs = {"timeout": timeout}
            if proxy:
                req_kwargs["proxy"] = proxy
            async with session.get(url, **req_kwargs) as response:
                if response.status != 404:
                    print(f"{Fore.GREEN}[+] {site:<12}: Ditemukan! -> {url}")
                    # Ambil detail profil jika diminta dan memungkinkan
                    if detail:
                        try:
                            text = await response.text()
                            snippet = text[:200].replace('\n',' ').replace('\r',' ')
                            print(Fore.CYAN + f"    [Detail] {snippet} ...")
                        except Exception:
                            print(Fore.YELLOW + "    [Detail] Gagal mengambil konten profil.")
                    return site, url
                else:
                    print(f"{Fore.RED}[-] {site:<12}: Tidak ditemukan.")
                    return site, None
        except asyncio.TimeoutError:
            print(f"{Fore.YELLOW}[!] {site:<12}: Timeout (percobaan {attempt+1}/{retry+1})")
            if log_error:
                log_error.write(f"Timeout: {site} {url}\n")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] {site:<12}: Error saat memeriksa (percobaan {attempt+1}/{retry+1})")
            if log_error:
                log_error.write(f"Error: {site} {url} | {e}\n")
        await asyncio.sleep(1)
    return site, None


async def main():
    """Fungsi utama untuk menjalankan program dengan fitur tambahan."""
    display_banner()

    parser = argparse.ArgumentParser(description="OSINT Username Checker by ReinsV")
    parser.add_argument('-u', '--username', help='Username yang akan diperiksa (atau path file list username)')
    parser.add_argument('-s', '--sites', help='Path file custom sites (format: Nama:URL)')
    parser.add_argument('-o', '--output', help='Nama file hasil output')
    parser.add_argument('--proxy', help='Proxy (http://ip:port atau socks5://ip:port)')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout request (detik)')
    parser.add_argument('--retry', type=int, default=2, help='Jumlah retry jika error/timeout')
    parser.add_argument('--detail', action='store_true', help='Ambil detail profil (snippet html)')
    parser.add_argument('--log', help='File log error')
    parser.add_argument('--max', type=int, default=8, help='Max concurrent request')
    args, unknown = parser.parse_known_args()

    # Multi-username dari file atau input
    usernames = []
    if args.username:
        if args.username.endswith('.txt'):
            try:
                with open(args.username, 'r') as f:
                    for line in f:
                        u = line.strip()
                        if u:
                            usernames.append(u)
            except Exception as e:
                print(Fore.RED + f"[!] Gagal membaca file username: {e}")
                return
        else:
            usernames = [args.username.strip()]
    else:
        inp = input("[?] Masukkan username (atau path file list username): ").strip()
        if inp.endswith('.txt'):
            try:
                with open(inp, 'r') as f:
                    for line in f:
                        u = line.strip()
                        if u:
                            usernames.append(u)
            except Exception as e:
                print(Fore.RED + f"[!] Gagal membaca file username: {e}")
                return
        else:
            usernames = [inp]

    # Validasi format username
    for username in usernames:
        if not re.match(r'^[A-Za-z0-9_.-]{3,32}$', username):
            print(f"{Fore.RED}[!] Format username tidak valid: {username}")
            return

    # Custom sites
    sites = DEFAULT_SITES
    if args.sites:
        sites = load_sites_from_file(args.sites)
    else:
        use_custom = input("[?] Gunakan daftar situs custom dari file? (y/n, default: n): ").strip().lower() == 'y'
        if use_custom:
            file_path = input("[?] Masukkan path file custom sites (format: Nama:URL): ").strip()
            sites = load_sites_from_file(file_path)

    # Output file
    save_file = False
    file_name = None
    if args.output:
        save_file = True
        file_name = args.output
    else:
        save_file = input("[?] Simpan hasil ke file? (y/n, default: n): ").strip().lower() == 'y'
        if save_file:
            file_name = input("[?] Nama file hasil (default: hasil_osint.txt): ").strip()
            if not file_name:
                file_name = "hasil_osint.txt"

    # Log error
    log_error = None
    if args.log:
        log_error = open(args.log, 'a')

    # Proxy
    proxy = args.proxy if args.proxy else None

    # Timeout, retry, max concurrent, detail
    timeout = args.timeout
    retry = args.retry
    max_concurrent = args.max
    detail = args.detail
    semaphore = asyncio.Semaphore(max_concurrent)

    all_results = {}
    for username in usernames:
        print(f"\n[*] Memeriksa username '{username}' di {len(sites)} website...\n")
        found_sites = []
        with tqdm(total=len(sites), desc=f"{username}", ncols=80) as pbar:
            async with aiohttp.ClientSession() as session:
                tasks = [limited_check(session, site, url_template, username, retry, timeout, proxy, log_error, detail, semaphore, pbar) for site, url_template in sites.items()]
                results = await asyncio.gather(*tasks)
                for site, url in results:
                    if url:
                        found_sites.append((site, url))
        all_results[username] = found_sites

    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}[*] Ringkasan Hasil Pemeriksaan:")
    for username in usernames:
        found_sites = all_results[username]
        if found_sites:
            print(f"{Fore.GREEN}Username '{username}' ditemukan di {len(found_sites)} situs:")
            for site, url in sorted(found_sites):
                print(f"  - {Fore.CYAN}{site:<12}: {url}")
        else:
            print(f"{Fore.YELLOW}Username '{username}' tidak ditemukan di situs manapun yang diperiksa.")
    print("=" * 60)

    # Simpan hasil ke file jika diminta
    if save_file and file_name:
        try:
            with open(file_name, 'w') as f:
                for username in usernames:
                    found_sites = all_results[username]
                    f.write(f"Ringkasan hasil pemeriksaan username: {username}\n")
                    if found_sites:
                        f.write(f"Ditemukan di {len(found_sites)} situs:\n")
                        for site, url in sorted(found_sites):
                            f.write(f"- {site:<12}: {url}\n")
                    else:
                        f.write("Tidak ditemukan di situs manapun.\n")
                    f.write("\n")
            print(f"{Fore.GREEN}[+] Hasil disimpan di {file_name}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Gagal menyimpan hasil ke file: {e}")
    if log_error:
        log_error.close()

async def limited_check(session, site, url_template, username, retry, timeout, proxy, log_error, detail, semaphore, pbar):
    async with semaphore:
        result = await check_username(session, site, url_template, username, retry, timeout, proxy, log_error, detail)
        pbar.update(1)
        return result


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Program dihentikan oleh pengguna.")