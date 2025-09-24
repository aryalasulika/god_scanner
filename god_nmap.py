import sys
try:
    import nmap
except ImportError:
    print("[!] Modul python-nmap tidak ditemukan. Install dengan: pip install python-nmap")
    sys.exit(1)
try:
    import pyfiglet
except ImportError:
    print("[!] Modul pyfiglet tidak ditemukan. Install dengan: pip install pyfiglet")
    sys.exit(1)

ORANGE = "\033[38;5;208m"
RESET = "\033[0m"

def display_banner():
    """Menampilkan banner program dengan warna orange dan info versi."""
    ascii_banner = pyfiglet.figlet_format("NMAP ASSISTANT")
    print(f"{ORANGE}{ascii_banner}{RESET}")
    print(f"{ORANGE}{'=' * 60}{RESET}")
    print(f"{ORANGE}        A Python Wrapper for Nmap by ReinsV{RESET}")
    print(f"{ORANGE}        Versi Tools : 1.1 | Python : {sys.version.split()[0]} | nmap : {get_nmap_version()}{RESET}")
    print(f"{ORANGE}        Dependensi  : python-nmap, pyfiglet{RESET}")
    print(f"{ORANGE}{'=' * 60}{RESET}")
    print(f"{ORANGE}\n{RESET}")

def get_nmap_version():
    try:
        return nmap.__version__
    except Exception:
        return "?"

def is_valid_ip(ip):
    try:
        import socket
        socket.inet_aton(ip)
        return True
    except Exception:
        return False

def is_valid_domain(domain):
    try:
        import socket
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

def run_scan(target, nmap_args, save_file=False, file_name=None):
    """Menjalankan scan Nmap berdasarkan argument pengguna."""
    try:
        nm = nmap.PortScanner()
    except nmap.PortScannerError:
        print(f"{ORANGE}[!] Nmap tidak ditemukan. Pastikan Nmap sudah terinstall di sistem Anda.{RESET}")
        sys.exit(1)

    print(f"{ORANGE}\n[*] Memulai scan pada target: {target}{RESET}")
    print(f"{ORANGE}[*] Argument Nmap: {nmap_args}{RESET}")
    print(f"{ORANGE}[*] Ini mungkin akan memakan waktu beberapa saat, mohon tunggu...{RESET}")

    # Cek hak akses admin/root
    is_admin = False
    try:
        import os
        if sys.platform.startswith('win'):
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            is_admin = os.geteuid() == 0
    except Exception:
        is_admin = False
    if not is_admin:
        print(f"{ORANGE}[!] Peringatan: Beberapa scan Nmap membutuhkan hak akses administrator/root!{RESET}")

    try:
        nm.scan(hosts=target, arguments=nmap_args)
    except Exception as e:
        print(f"{ORANGE}[!] Terjadi error saat scan: {e}{RESET}")
        return

    hasil_scan = []
    hasil_scan.append("\n" + "=" * 30)
    hasil_scan.append("HASIL PEMINDAIAN")
    hasil_scan.append("=" * 30)

    if not nm.all_hosts():
        hasil_scan.append(f"[!] Tidak dapat menemukan informasi untuk host: {target}")
        print(f"{ORANGE}[!] Tidak dapat menemukan informasi untuk host: {target}{RESET}")
        if save_file and file_name:
            with open(file_name, 'w') as f:
                f.write('\n'.join(hasil_scan))
        return

    for host in nm.all_hosts():
        hasil_scan.append(f"\n[+] Host: {host} ({nm[host].hostname()})")
        hasil_scan.append(f"    State: {nm[host].state()}")

        for proto in nm[host].all_protocols():
            hasil_scan.append(f"\n    Protocol: {proto.upper()}")
            ports = nm[host][proto].keys()
            for port in sorted(ports):
                service_info = nm[host][proto][port]
                state = service_info['state']
                name = service_info['name']
                product = service_info.get('product', '')
                version = service_info.get('version', '')
                # Pewarnaan status port
                if state == 'open':
                    color = '\033[38;5;208m'  # orange
                elif state == 'closed':
                    color = '\033[31m'  # red
                elif state == 'filtered':
                    color = '\033[33m'  # yellow
                else:
                    color = RESET
                hasil_scan.append(f"      Port: {port:<6} | State: {color}{state:<9}{RESET} | Service: {name} {product} {version}")

    # Tampilkan hasil dengan warna
    for line in hasil_scan:
        print(f"{ORANGE}{line}{RESET}" if 'Port:' not in line else line)
    # Simpan ke file jika diminta
    if save_file and file_name:
        try:
            with open(file_name, 'w') as f:
                for line in hasil_scan:
                    # Hilangkan escape code warna saat simpan ke file
                    f.write(line.replace('\033[38;5;208m','').replace('\033[31m','').replace('\033[33m','').replace(RESET,'') + '\n')
            print(f"{ORANGE}[+] Hasil disimpan di {file_name}{RESET}")
        except Exception as e:
            print(f"{ORANGE}[!] Gagal menyimpan hasil ke file: {e}{RESET}")

def main():
    display_banner()

    target = input(f"{ORANGE}[?] Masukkan Target (IP atau Domain): {RESET}").strip()
    if not target:
        print(f"{ORANGE}[!] Target tidak boleh kosong. Program berhenti.{RESET}")
        return
    if not (is_valid_ip(target) or is_valid_domain(target)):
        print(f"{ORANGE}[!] Target '{target}' tidak valid. Program berhenti.{RESET}")
        return

    print(f"{ORANGE}\nPilih Jenis Scan yang Diinginkan:{RESET}")
    print(f"{ORANGE}  1. Ping Scan         (Cek apakah target hidup/online){RESET}")
    print(f"{ORANGE}  2. Regular Scan      (Scan cepat 1000 port umum & deteksi versi){RESET}")
    print(f"{ORANGE}  3. Intense Scan      (Scan lambat tapi sangat detail ke semua 65535 port){RESET}")
    print(f"{ORANGE}  4. Custom Argument   (Masukkan argument Nmap sendiri){RESET}")

    choice = input(f"{ORANGE}\n[?] Masukkan pilihan Anda (1/2/3/4): {RESET}").strip()

    nmap_args = ""
    if choice == '1':
        nmap_args = '-sn'
    elif choice == '2':
        nmap_args = '-sV'
    elif choice == '3':
        nmap_args = '-p- -T4 -A -v'
    elif choice == '4':
        nmap_args = input(f"{ORANGE}[?] Masukkan argument Nmap custom (misal: -sS -O -p 80,443): {RESET}").strip()
        if not nmap_args:
            print(f"{ORANGE}[!] Argument Nmap tidak boleh kosong. Program berhenti.{RESET}")
            return
    else:
        print(f"{ORANGE}[!] Pilihan tidak valid. Program berhenti.{RESET}")
        return

    save_file = input(f"{ORANGE}[?] Simpan hasil ke file? (y/n, default: n): {RESET}").strip().lower() == 'y'
    file_name = None
    if save_file:
        file_name = input(f"{ORANGE}[?] Nama file hasil (default: hasil_nmap.txt): {RESET}").strip()
        if not file_name:
            file_name = "hasil_nmap.txt"

    run_scan(target, nmap_args, save_file, file_name)

if __name__ == "__main__":
    main()