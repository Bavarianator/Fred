# OmniBackup 🛡️

**Das ultimative Backup-Tool – simpler als Time Machine, mächtiger als Borg/Restic/Kopia**

[![Crates.io](https://img.shields.io/crates/v/omnibackup.svg)](https://crates.io/crates/omnibackup)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://rust-lang.org)

---

## 🎯 Features

### ✨ Kernfunktionen

- **🔐 Verschlüsselt by Default** – age (X25519) + ChaCha20-Poly1305 + Argon2id
- **📦 Deduplizierung** – FastCDC Content-Defined Chunking mit BLAKE3
- **🗜️ Kompression** – Adaptive ZSTD-Kompression (Level 1-22)
- **✅ Integrity** – Merkle-Tree-Verification für Self-Healing
- **☁️ 70+ Cloud-Backends** – S3, B2, R2, Azure, GCS, Nextcloud, WebDAV, SFTP...
- **🌐 P2P-Backup** – Dezentral mit libp2p, QUIC, Erasure-Coding
- **🖥️ Wunderschöne TUI** – Catppuccin-Theme, Live-Status, 60 FPS
- **⏰ Smart Scheduling** – Continuous, USB-Trigger, Idle-Detection
- **🔔 Notifications** – Desktop, Webhook, Telegram, Discord, ntfy.sh
- **📀 FUSE-Mount** – Snapshots als Dateisystem einhängen

### 🚀 Killer-Features

| Feature | Beschreibung |
|---------|-------------|
| **Smart Source Detection** | Erkennt automatisch wichtige Verzeichnisse & Anti-Patterns |
| **App-Aware Backups** | Browser-Profile, Mail-Clients, Datenbanken, Git-Repos |
| **Time-Machine-Mode** | Slider-UI: "Wie sahen meine Dateien am 15. Januar aus?" |
| **Bandwidth-Smart** | Auto-Throttle bei Video-Calls, Metered-Connection-Detection |
| **Cost-Awareness** | Live-Kostenrechner pro Cloud-Backend |
| **Disaster-Recovery** | Bootable ISO, QR-Code-Recovery, Bare-Metal-Restore |
| **Forever-Compatible** | Open Format-Spec v1.0 = ewig lesbar (auch ohne OmniBackup) |

---

## 📦 Installation

### Aus den Quellen

```bash
git clone https://github.com/omnibackup/omnibackup.git
cd omnibackup
cargo build --release
sudo cp target/release/omnibackup /usr/local/bin/
```

### Mit Cargo

```bash
cargo install omnibackup
```

### Pre-built Binaries

- **Linux**: `.deb`, `.rpm`, `AppImage`
- **macOS**: `.dmg`, Homebrew (`brew install omnibackup`)
- **Windows**: `.msi`, Chocolatey (`choco install omnibackup`)

---

## 🚀 Quick Start

### 1. Erststart mit Wizard

```bash
omnibackup
```

Der interaktive Wizard führt dich durch:
1. **Quellen auswählen** – Automatische Erkennung wichtiger Verzeichnisse
2. **Ziele wählen** – Lokal, Cloud, P2P oder Hybrid (3-2-1-Regel)
3. **Verschlüsselung** – Starkes Passwort setzen
4. **Zeitplan** – Kontinuierlich, stündlich, täglich
5. **Fertig!** – Erstes Backup startet

### 2. CLI-Befehle

```bash
# Backup manuell starten
omnibackup backup

# Wiederherstellen (interaktiv)
omnibackup restore

# Snapshots anzeigen
omnibackup snapshots list

# Snapshot mounten (FUSE)
omnibackup mount latest /mnt/backup

# System-Check
omnibackup doctor
```

---

## 🎨 TUI Screenshots

### Hauptansicht (Dashboard)

```
┌─ OmniBackup v1.0 ─────────────────────[⚡ Online | 🔒 Encrypted | 🌐 3 Peers]─┐
│                                                                                │
│ ┌─ Quellen ──────────┐ ┌─ Live-Status ──────────────────────────────────────┐│
│ │ ▸ 📁 ~/Documents   │ │ 🔄 Sichere: ~/Pictures/2024/urlaub_griechenland/   ││
│ │   2.3 GB ✓         │ │    📷 IMG_4521.jpg (4.2 MB)                        ││
│ │ ▸ 📁 ~/Pictures    │ │                                                     ││
│ │   15.7 GB 🔄       │ │ [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░] 80%                          ││
│ │ ▸ 📁 ~/Projects    │ │                                                     ││
│ │   1.2 GB ⏸         │ │ Fortschritt: 12.6 GB / 15.7 GB                     ││
│ │ ▸ ⚙  ~/.config     │ │ Geschwindigkeit: ▁▂▃▅▆▇█ 45.3 MB/s                 ││
│ │   45 MB ✓          │ │ Verbleibend: 00:01:08                              ││
│ │                    │ │ Chunks: 12,345 │ Dedup: 32% gespart                ││
│ │ + Quelle hinzu...  │ │ Komprimiert: 8.4 GB → 67% Ratio                    ││
│ └────────────────────┘ └─────────────────────────────────────────────────────┘│
│                                                                                │
│ ┌─ Ziele ────────────┐ ┌─ Snapshots ─────────────────────────────────────────┐│
│ │ ☁  B2 (eu-central) │ │ 📅 2025-01-15 14:23 │ 4.2 GB │ ✓ │ daily, latest    ││
│ │   ▓▓▓▓▓▓▓░ 78%     │ │ 📅 2025-01-15 13:08 │ 4.1 GB │ ✓ │ hourly           ││
│ │ 🏠 Nextcloud       │ │ 📅 2025-01-15 12:00 │ 4.1 GB │ ✓ │ hourly           ││
│ │   ▓▓▓▓▓▓▓▓ 100% ✓  │ │ 📅 2025-01-14 14:20 │ 4.0 GB │ ✓ │ daily            ││
│ │ 💾 /mnt/backup     │ │ 📅 2025-01-13 14:18 │ 3.9 GB │ ✓ │ daily            ││
│ │   ▓▓▓▓▓▓▓▓ 100% ✓  │ │ 📅 2025-01-08 14:15 │ 3.8 GB │ ✓ │ weekly           ││
│ │ 🌐 P2P (3 peers)   │ │ 📅 2025-01-01 14:10 │ 3.5 GB │ ✓ │ monthly          ││
│ │   ▓▓▓▓▓▓░░ 65%     │ │                                                     ││
│ └────────────────────┘ └─────────────────────────────────────────────────────┘│
│                                                                                │
│ 📊 Heute: 234 Dateien │ 12.4 GB │ 8 min │ Erfolgsrate: 100%                  │
│                                                                                │
│ [F1]Hilfe [F2]Backup [F3]Wiederherstellen [F4]Snapshots [F5]P2P [F6]⚙ [Q]uit │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 Dokumentation

- **[FORMAT_SPEC.md](docs/FORMAT_SPEC.md)** – Repository-Format-Spezifikation (ewig kompatibel)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** – System-Architektur
- **[PLUGIN_API.md](docs/PLUGIN_API.md)** – Plugin-Entwicklung

---

## 🛠️ Tech Stack

| Komponente | Technologie |
|-----------|------------|
| **Sprache** | Rust (Stable, MSRV 1.75+) |
| **TUI** | ratatui + crossterm |
| **Async** | tokio (multi-threaded) |
| **DB** | SQLite via sqlx |
| **Crypto** | age, ChaCha20-Poly1305, Argon2id |
| **Hash** | BLAKE3 |
| **Compression** | zstd (adaptiv) |
| **Chunking** | FastCDC |
| **P2P** | libp2p (QUIC, Noise, Kademlia) |
| **Storage** | OpenDAL (70+ Backends) |
| **FUSE** | fuser |
| **Config** | TOML + JSON-Schema |

---

## 🔐 Security

- **Verschlüsselung:** age (X25519) + ChaCha20-Poly1305
- **Key-Derivation:** Argon2id (OWASP 2024 Parameter)
- **Integrity:** BLAKE3 Merkle-Trees
- **Self-Healing:** Reed-Solomon Erasure-Coding (P2P)
- **Audit:** Alle Operationen geloggt (optional JSON)

---

## 🌍 Supported Backends

### First-Class Native

- AWS S3 (Glacier, IA, Intelligent-Tiering)
- Backblaze B2
- Cloudflare R2 (Zero Egress)
- Wasabi (Hot-Storage Flat-Rate)
- Azure Blob Storage
- Google Cloud Storage
- Nextcloud / ownCloud
- MinIO
- WebDAV
- SFTP/SSH

### Via OpenDAL (70+)

Google Drive, Dropbox, OneDrive, pCloud, Mega, Yandex Disk, Box.com, iCloud Drive, Oracle Cloud, IBM COS, Alibaba OSS, Tencent COS, Hugging Face Hub, IPFS, GitHub, und viele mehr...

---

## 🤝 Contributing

Contributions sind willkommen! Bitte lese zuerst:

1. [CONTRIBUTING.md](.github/CONTRIBUTING.md)
2. [Code of Conduct](.github/CODE_OF_CONDUCT.md)

### Entwicklung starten

```bash
git clone https://github.com/omnibackup/omnibackup.git
cd omnibackup
cargo test
cargo run
```

---

## 📄 License

- **Open Source:** AGPL-3.0-or-later
- **Commercial:** Kontaktiere uns für Enterprise-Lizenzen

---

## 🙏 Credits

Inspiriert von:
- [BorgBackup](https://www.borgbackup.org/)
- [Restic](https://restic.net/)
- [Kopia](https://kopia.io/)
- [Duplicacy](https://duplicacy.com/)
- [Time Machine](https://www.apple.com/macos/time-machine/)

---

**OmniBackup** – Es funktioniert einfach. Für jeden. Überall. Für immer. 🚀
