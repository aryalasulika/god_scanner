#!/usr/bin/env python3

import socket
from threading import Thread, Lock
from queue import Queue
try:
    import pyfiglet
except ImportError:
    print("[!] Modul pyfiglet tidak ditemukan. Install dengan: pip install pyfiglet")
    exit(1)


# ANSI escape untuk warna orange
ORANGE = "\033[38;5;208m"
RESET = "\033[0m"

# Antrian untuk port yang akan dipindai
q = Queue()
# List untuk menyimpan port yang terbuka
open_ports = []
# Lock untuk sinkronisasi output
print_lock = Lock()

def display_banner():
    """Menampilkan banner program dengan warna orange."""
    ascii_banner = pyfiglet.figlet_format("GOD SCANNER")
    print(f"{ORANGE}{ascii_banner}{RESET}")
    print(f"{ORANGE}{'=' * 60}{RESET}")
    print(f"{ORANGE}        GOD SCANNER BY ReinsV{RESET}")
    print(f"{ORANGE}        Interactive Port Scanner{RESET}")
    print(f"{ORANGE}{'=' * 60}{RESET}")
    print(f"{ORANGE}\n{RESET}")

def scan_port(port, target):
    """
    Fungsi untuk memindai satu port.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        conn = s.connect_ex((target, port))
        if conn == 0:
            with print_lock:
                print(f"{ORANGE}[+] Port {port:<5} is open{RESET}")
                open_ports.append(port)
    except Exception as e:
        pass
    finally:
        s.close()

def worker(target):
    """Fungsi pekerja yang mengambil port dari antrian dan memindainya."""
    while not q.empty():
        port = q.get()
        scan_port(port, target)
        q.task_done()

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def is_valid_domain(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.error:
        return False

def is_valid_port(port):
    return 1 <= port <= 65535

def main():
    display_banner()
    
    # --- PERUBAHAN UTAMA ADA DI SINI ---
    # Meminta input dari pengguna secara interaktif
    target = input(f"{ORANGE}[?] Masukkan Target (IP atau Domain): {RESET}").strip()
    if not target:
        print(f"{ORANGE}[!] Target tidak boleh kosong. Program berhenti.{RESET}")
        return
    if not (is_valid_ip(target) or is_valid_domain(target)):
        print(f"{ORANGE}[!] Target '{target}' tidak valid. Program berhenti.{RESET}")
        return

    port_range_str = input(f"{ORANGE}[?] Masukkan Port (misal: 1-1024 atau 80,443,22): {RESET}").strip()
    if not port_range_str:
        port_range_str = "1-1024" # Default jika pengguna tidak mengisi
        print(f"{ORANGE}[*] Tidak ada port spesifik, menggunakan default: {port_range_str}{RESET}")

    thread_input = input(f"{ORANGE}[?] Masukkan Jumlah Thread (default: 100): {RESET}").strip()
    num_threads = int(thread_input) if thread_input.isdigit() else 100

    save_file = input(f"{ORANGE}[?] Simpan hasil ke file? (y/n, default: n): {RESET}").strip().lower() == 'y'
    file_name = None
    if save_file:
        file_name = input(f"{ORANGE}[?] Nama file hasil (default: hasil_scan.txt): {RESET}").strip()
        if not file_name:
            file_name = "hasil_scan.txt"
    # --- AKHIR DARI PERUBAHAN ---

    print(f"{ORANGE}\n{'=' * 60}{RESET}")
    print(f"{ORANGE}[*] Memulai pemindaian pada target: {target}{RESET}")
    print(f"{ORANGE}[*] Jangkauan port: {port_range_str}{RESET}")
    print(f"{ORANGE}[*] Menggunakan {num_threads} threads.{RESET}")
    print(f"{ORANGE}{'=' * 60}\n{RESET}")

    # Parsing port range
    try:
        if '-' in port_range_str:
            start, end = map(int, port_range_str.split('-'))
            if not (is_valid_port(start) and is_valid_port(end)) or start > end:
                print(f"{ORANGE}[!] Range port tidak valid. Program berhenti.{RESET}")
                return
            for port in range(start, end + 1):
                if is_valid_port(port):
                    q.put(port)
        else:
            ports = [int(p.strip()) for p in port_range_str.split(',')]
            for port in ports:
                if not is_valid_port(port):
                    print(f"{ORANGE}[!] Port {port} tidak valid. Program berhenti.{RESET}")
                    return
                q.put(port)
    except ValueError:
    print(f"{ORANGE}[!] Format port yang Anda masukkan salah. Program berhenti.{RESET}")
    return

    # Membuat dan memulai threads
    for _ in range(num_threads):
        thread = Thread(target=worker, args=(target,))
        thread.daemon = True
        thread.start()
    
    q.join()

    print(f"{ORANGE}\n[+] Pemindaian selesai!{RESET}")
    print(f"{ORANGE}[+] Port yang terbuka: {sorted(open_ports)}{RESET}")
    if save_file:
        try:
            with open(file_name, 'w') as f:
                f.write(f"Target: {target}\n")
                f.write(f"Port terbuka: {sorted(open_ports)}\n")
            print(f"{ORANGE}[+] Hasil disimpan di {file_name}{RESET}")
        except Exception as e:
            print(f"{ORANGE}[!] Gagal menyimpan hasil ke file: {e}{RESET}")

if __name__ == "__main__":
    main()