
import sys
import re
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
    from colorama import init, Fore
except ImportError:
    print("[!] Modul colorama belum terinstall. Install dengan: pip install colorama")
    sys.exit(1)

# Inisialisasi Colorama
init(autoreset=True)

def display_banner():
    """Menampilkan banner program dan info versi."""
    ascii_banner = pyfiglet.figlet_format("USER CHECKER")
    print(Fore.YELLOW + ascii_banner)
    print(Fore.YELLOW + "=" * 60)
    print(Fore.YELLOW + "        Simple OSINT Username Checker by ReinsV")
    print(Fore.YELLOW + f"        Versi Tools : 1.1 | Python : {sys.version.split()[0]}")
    print(Fore.YELLOW + "        Dependensi  : aiohttp, pyfiglet, colorama")
    print(Fore.YELLOW + "=" * 60)
    print(Fore.YELLOW + "\n")


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

async def check_username(session, site, url_template, username, retry=2):
    """
    Fungsi async untuk memeriksa satu username di satu situs, dengan retry.
    """
    url = url_template.format(username)
    for attempt in range(retry+1):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 404:
                    print(f"{Fore.GREEN}[+] {site:<12}: Ditemukan! -> {url}")
                    return site, url
                else:
                    print(f"{Fore.RED}[-] {site:<12}: Tidak ditemukan.")
                    return site, None
        except asyncio.TimeoutError:
            print(f"{Fore.YELLOW}[!] {site:<12}: Timeout (percobaan {attempt+1}/{retry+1})")
        except Exception:
            print(f"{Fore.YELLOW}[!] {site:<12}: Error saat memeriksa (percobaan {attempt+1}/{retry+1})")
        await asyncio.sleep(1)
    return site, None

async def main():
    """Fungsi utama untuk menjalankan program."""
    display_banner()
    username = input("[?] Masukkan username yang akan diperiksa: ").strip()

    # Validasi format username (alfanumerik dan _ . -)
    if not username:
        print(f"{Fore.RED}[!] Username tidak boleh kosong.")
        return
    if not re.match(r'^[A-Za-z0-9_.-]{3,32}$', username):
        print(f"{Fore.RED}[!] Format username tidak valid. Hanya huruf, angka, _ . - dan panjang 3-32 karakter.")
        return

    # Opsi custom sites
    use_custom = input("[?] Gunakan daftar situs custom dari file? (y/n, default: n): ").strip().lower() == 'y'
    sites = DEFAULT_SITES
    if use_custom:
        file_path = input("[?] Masukkan path file custom sites (format: Nama:URL): ").strip()
        sites = load_sites_from_file(file_path)

    print(f"\n[*] Memeriksa username '{username}' di {len(sites)} website...\n")

    found_sites = []
    save_file = input("[?] Simpan hasil ke file? (y/n, default: n): ").strip().lower() == 'y'
    file_name = None
    if save_file:
        file_name = input("[?] Nama file hasil (default: hasil_osint.txt): ").strip()
        if not file_name:
            file_name = "hasil_osint.txt"

    # Limitasi request (max concurrent)
    max_concurrent = 8
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_check(session, site, url_template, username):
        async with semaphore:
            return await check_username(session, site, url_template, username)

    async with aiohttp.ClientSession() as session:
        tasks = [limited_check(session, site, url_template, username) for site, url_template in sites.items()]
        results = await asyncio.gather(*tasks)
        for site, url in results:
            if url:
                found_sites.append((site, url))

    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}[*] Ringkasan Hasil Pemeriksaan:")
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
                f.write(f"Ringkasan hasil pemeriksaan username: {username}\n")
                if found_sites:
                    f.write(f"Ditemukan di {len(found_sites)} situs:\n")
                    for site, url in sorted(found_sites):
                        f.write(f"- {site:<12}: {url}\n")
                else:
                    f.write("Tidak ditemukan di situs manapun.\n")
            print(f"{Fore.GREEN}[+] Hasil disimpan di {file_name}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Gagal menyimpan hasil ke file: {e}")


if __name__ == "__main__":
    # Menjalankan loop event asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Program dihentikan oleh pengguna.")