#!/usr/bin/env python3

import socket
from threading import Thread, Lock
from queue import Queue
import pyfiglet

# Antrian untuk port yang akan dipindai
q = Queue()
# List untuk menyimpan port yang terbuka
open_ports = []
# Lock untuk sinkronisasi output
print_lock = Lock()

def display_banner():
    """Menampilkan banner program."""
    ascii_banner = pyfiglet.figlet_format("GOD SCANNER")
    print(ascii_banner)
    print("=" * 60)
    print("        GOD SCANNER BY ReinsV")
    print("        Interactive Port Scanner")
    print("=" * 60)
    print("\n")

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
                print(f"[+] Port {port:<5} is open")
                open_ports.append(port)
    except Exception:
        pass
    finally:
        s.close()

def worker(target):
    """Fungsi pekerja yang mengambil port dari antrian dan memindainya."""
    while not q.empty():
        port = q.get()
        scan_port(port, target)
        q.task_done()

def main():
    display_banner()
    
    # --- PERUBAHAN UTAMA ADA DI SINI ---
    # Meminta input dari pengguna secara interaktif
    target = input("[?] Masukkan Target (IP atau Domain): ").strip()
    if not target:
        print("[!] Target tidak boleh kosong. Program berhenti.")
        return

    port_range_str = input("[?] Masukkan Port (misal: 1-1024 atau 80,443,22): ").strip()
    if not port_range_str:
        port_range_str = "1-1024" # Default jika pengguna tidak mengisi
        print(f"[*] Tidak ada port spesifik, menggunakan default: {port_range_str}")

    thread_input = input("[?] Masukkan Jumlah Thread (default: 100): ").strip()
    num_threads = int(thread_input) if thread_input.isdigit() else 100
    # --- AKHIR DARI PERUBAHAN ---

    print("\n" + "=" * 60)
    print(f"[*] Memulai pemindaian pada target: {target}")
    print(f"[*] Jangkauan port: {port_range_str}")
    print(f"[*] Menggunakan {num_threads} threads.")
    print("=" * 60 + "\n")

    # Parsing port range
    try:
        if '-' in port_range_str:
            start, end = map(int, port_range_str.split('-'))
            for port in range(start, end + 1):
                q.put(port)
        else:
            ports = [int(p.strip()) for p in port_range_str.split(',')]
            for port in ports:
                q.put(port)
    except ValueError:
        print("[!] Format port yang Anda masukkan salah. Program berhenti.")
        return

    # Membuat dan memulai threads
    for _ in range(num_threads):
        thread = Thread(target=worker, args=(target,))
        thread.daemon = True
        thread.start()
    
    q.join()

    print("\n[+] Pemindaian selesai!")
    print(f"[+] Port yang terbuka: {sorted(open_ports)}")

if __name__ == "__main__":
    main()