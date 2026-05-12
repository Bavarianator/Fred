# OmniBackup Repository Format Specification v1.0

**Status:** Final  
**Effective Date:** 2025-01-15  
**Compatibility:** Forever (guaranteed backward compatible)

## 🎯 Design Goals

1. **Ewig lesbar** – Auch ohne OmniBackup-Software wiederherstellbar
2. **Content-Addressed** – BLAKE3-Hashes als primäre Referenz
3. **Verschlüsselt by Default** – age (X25519) + ChaCha20-Poly1305
4. **Dedupliziert** – Chunk-basiert mit FastCDC
5. **Self-Describing** – Alle Metadaten im Repository enthalten
6. **Verifizierbar** – Merkle-Tree für Integrity-Checks
7. **Erweiterbar** – Neue Features ohne Breaking Changes

---

## 📁 Repository-Struktur

```
my-backup-repo/
├── omnibackup.toml              # Repo-Metadata (Format-Version, Config)
├── RECOVERY.txt                 # Plaintext-Anleitung zur manuellen Wiederherstellung
├── keys/
│   └── master.age               # Mit Passwort verschlüsselter Master-Key
├── index/
│   ├── snapshots.db             # SQLite-Index aller Snapshots
│   ├── chunks.db                # Chunk-Lookup-Tabelle
│   └── manifest.json.age        # Verschlüsseltes Gesamt-Manifest
├── chunks/                      # Content-Addressed Storage (CAS)
│   ├── ab/
│   │   └── ab3f8c2e...blake3.zst.age    # 2-stelliges Prefix für Skalierung
│   ├── cd/
│   │   └── cd9e1a4b...blake3.zst.age
│   └── ...
├── snapshots/
│   ├── 2025-01-15_142300_abc123.json.age
│   ├── 2025-01-14_142000_def456.json.age
│   └── ...
└── logs/
    └── backup-2025-01-15.log    # Backup-Protokoll (optional)
```

---

## 📄 Datei-Spezifikationen

### `omnibackup.toml` (Repo-Metadata)

```toml
# OmniBackup Repository Metadata
format_version = "1.0"
format_spec_url = "https://omnibackup.dev/spec/v1.0"
created_at = "2025-01-15T14:23:00Z"
created_by = "omnibackup v1.0.0"

[repo]
id = "550e8400-e29b-41d4-a716-446655440000"
name = "My Personal Backup"
description = "Backup of all important files"

[crypto]
algorithm = "age-x25519"
kdf = "argon2id"
kdf_memory_kb = 65536
kdf_iterations = 3
kdf_parallelism = 4

[compression]
algorithm = "zstd"
level = 12

[chunking]
algorithm = "fastcdc"
min_size = 262144      # 256 KB
avg_size = 1048576     # 1 MB
max_size = 4194304     # 4 MB

[deduplication]
hash = "blake3"
hash_length = 32       # 256 bits

[verification]
merkle_tree = true
tree_hash = "blake3"

[storage]
layout = "prefix-2char"  # chunks/ab/cdef1234...
```

---

### `RECOVERY.txt` (Manuelle Wiederherstellung)

Dies ist eine **Plaintext-Datei** mit Anleitungen zur Wiederherstellung OHNE OmniBackup.

```
╔══════════════════════════════════════════════════════════════════╗
║          OmniBackup Recovery Manual – No Software Required       ║
╚══════════════════════════════════════════════════════════════════╝

This repository uses open standards. You can recover your data with
standard tools: age, zstd, blake3sum, and tar.

PREREQUISITES:
  - age (https://age-encryption.org)
  - zstd (https://facebook.github.io/zstd)
  - blake3 (https://github.com/BLAKE3-team/BLAKE3)
  - tar (GNU tar)

STEP 1: Decrypt the Master Key
────────────────────────────────
  age --decrypt --passphrase keys/master.age > master_key.bin

STEP 2: List Available Snapshots
─────────────────────────────────
  for f in snapshots/*.json.age; do
    age --decrypt --identity master_key.bin "$f" | jq '.created_at'
  done

STEP 3: Extract a Snapshot Manifest
────────────────────────────────────
  age --decrypt --identity master_key.bin snapshots/2025-01-15_*.json.age \
    | jq '.' > manifest.json

STEP 4: Download and Decrypt Chunks
────────────────────────────────────
  # Example for a single file from manifest.json:
  # {"path": "/home/user/doc.pdf", "chunks": [
  #   {"hash": "ab3f8c2e...", "size": 1048576},
  #   {"hash": "cd9e1a4b...", "size": 524288}
  # ]}

  for chunk_hash in ab3f8c2e cd9e1a4b; do
    prefix=${chunk_hash:0:2}
    age --decrypt --identity master_key.bin \
      "chunks/$prefix/$chunk_hash.blake3.zst.age" | \
    zstd -d > "chunk_$chunk_hash"
  done

STEP 5: Verify Integrity (Optional)
────────────────────────────────────
  blake3sum chunk_ab3f8c2e
  # Should match: ab3f8c2e...

STEP 6: Reassemble Files
─────────────────────────
  cat chunk_ab3f8c2e chunk_cd9e1a4b > restored_doc.pdf

FOR MORE INFORMATION:
  https://omnibackup.dev/recovery

Repository ID: 550e8400-e29b-41d4-a716-446655440000
Created: 2025-01-15T14:23:00Z
```

---

### Chunk-Format (`chunks/{prefix}/{hash}.blake3.zst.age`)

Jeder Chunk durchläuft diese Pipeline:

```
Raw Data (variable size, 256KB–4MB)
    ↓
[BLAKE3 Hash] ← wird zum Dateinamen
    ↓
[ZSTD Compression] → Level 1-22 (adaptiv)
    ↓
[ChaCha20-Poly1305 Encryption] ← mit Chunk-Key
    ↓
[AGE Encoding] ← mit Repository Master-Key
    ↓
File: {prefix}/{blake3-hash}.blake3.zst.age
```

**Chunk-Key Derivation:**
```
chunk_key = HKDF-SHA256(master_key, salt=chunk_hash, info="omnibackup-chunk-v1")
```

---

### Snapshot-Format (`snapshots/{timestamp}_{id}.json.age`)

```json
{
  "snapshot_id": "abc123def456",
  "created_at": "2025-01-15T14:23:00Z",
  "hostname": "my-laptop",
  "username": "alice",
  "os": "Linux 6.7.0-arch1-1",
  "omnibackup_version": "1.0.0",
  
  "sources": [
    {
      "path": "/home/alice/Documents",
      "type": "directory",
      "total_files": 1234,
      "total_bytes": 2456789012,
      "chunk_count": 2345
    }
  ],
  
  "files": [
    {
      "path": "/home/alice/Documents/report.pdf",
      "type": "file",
      "size": 1048576,
      "mode": "0644",
      "uid": 1000,
      "gid": 1000,
      "mtime": "2025-01-14T10:30:00Z",
      "atime": "2025-01-15T09:00:00Z",
      "ctime": "2025-01-14T10:30:00Z",
      "hash": "blake3:abc123...",
      "chunks": [
        {
          "hash": "ab3f8c2e1d5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
          "offset": 0,
          "size": 1048576,
          "compressed_size": 655360
        }
      ],
      "symlink_target": null,
      "xattrs": {
        "user.comment": "Important document"
      }
    }
  ],
  
  "stats": {
    "total_files": 1234,
    "total_dirs": 56,
    "total_symlinks": 12,
    "total_bytes": 2456789012,
    "unique_chunks": 2345,
    "deduplicated_chunks": 456,
    "dedup_ratio": 0.82,
    "compressed_size": 1610612736,
    "compression_ratio": 0.67,
    "duration_seconds": 123,
    "throughput_mbps": 45.6
  },
  
  "tags": ["daily", "auto"],
  "notes": "",
  
  "merkle_root": "blake3:xyz789..."
}
```

---

### SQLite-Schema (`index/snapshots.db`)

```sql
-- Snapshots Tabelle
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    hostname TEXT NOT NULL,
    username TEXT NOT NULL,
    source_count INTEGER NOT NULL,
    file_count INTEGER NOT NULL,
    total_bytes INTEGER NOT NULL,
    compressed_bytes INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    tags TEXT,  -- JSON array
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    merkle_root TEXT NOT NULL
);

-- Files Tabelle
CREATE TABLE files (
    snapshot_id TEXT NOT NULL,
    path TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'file', 'directory', 'symlink'
    size INTEGER,
    mode TEXT,
    uid INTEGER,
    gid INTEGER,
    mtime TIMESTAMP,
    hash TEXT,
    chunk_count INTEGER,
    PRIMARY KEY (snapshot_id, path),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

-- Chunks Tabelle (global, dedupliziert)
CREATE TABLE chunks (
    hash TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    compressed_size INTEGER,
    ref_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL
);

-- File-Chunks Mapping
CREATE TABLE file_chunks (
    snapshot_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_hash TEXT NOT NULL,
    offset INTEGER NOT NULL,
    size INTEGER NOT NULL,
    PRIMARY KEY (snapshot_id, file_path, chunk_index),
    FOREIGN KEY (chunk_hash) REFERENCES chunks(hash)
);

-- Indizes für Performance
CREATE INDEX idx_files_snapshot ON files(snapshot_id);
CREATE INDEX idx_files_path ON files(path);
CREATE INDEX idx_chunks_refcount ON chunks(ref_count);
CREATE INDEX idx_file_chunks_hash ON file_chunks(chunk_hash);

-- Schema Version Tracking
CREATE TABLE schema_info (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_info (version) VALUES (1);
```

---

## 🔐 Kryptographie-Spezifikation

### Master-Key Generierung

```rust
// Argon2id Parameter (OWASP 2024 Empfehlungen)
memory_size: 64 MB
iterations: 3
parallelism: 4
output_length: 32 bytes

// PBKDF: Argon2id(password, salt=random(16 bytes))
// Result: 32-byte master key
```

### Chunk-Verschlüsselung

```rust
// Algorithm: ChaCha20-Poly1305
// Key Derivation: HKDF-SHA256(master_key, salt=chunk_hash, info="omnibackup-chunk-v1")
// Nonce: First 12 bytes of BLAKE3(chunk_hash + counter)
```

### Age-Integration

```
Recipient: X25519 public key (abgeleitet von master_key)
Identity: X25519 private key (verschlüsselt mit Passwort via Argon2id)
```

---

## ✅ Integrity & Verification

### Merkle-Tree Aufbau

```
Snapshot Root Hash = BLAKE3(
    concat(
        BLAKE3(file1_metadata + file1_chunk_hashes),
        BLAKE3(file2_metadata + file2_chunk_hashes),
        ...
    )
)
```

### Verification Steps

1. **Chunk-Level:** BLAKE3-Hash nach Decryption+Decompression prüfen
2. **File-Level:** Alle Chunk-Hashes verifizieren
3. **Snapshot-Level:** Merkle-Root berechnen und vergleichen
4. **Repository-Level:** Alle Snapshots iterieren, konsistenz prüfen

---

## 🔄 Versionierung & Migration

### Format-Versionen

| Version | Datum | Änderungen | Kompatibilität |
|---------|-------|-----------|----------------|
| 1.0 | 2025-01-15 | Initial Release | - |

### Migrations-Regeln

1. **Minor Updates (1.x):** Immer vorwärts-kompatibel
2. **Major Updates (2.0):** Erfordern Migration, alte Repos bleiben lesbar
3. **Deprecation Policy:** Alte Versionen werden mind. 5 Jahre unterstützt

---

## 🌍 Open Source Guarantee

Diese Spezifikation ist **öffentlich und lizenzfrei** implementierbar:

- **Spec-Dokument:** CC-BY-SA 4.0
- **Referenz-Implementation:** AGPL-3.0-or-later
- **Test-Vektoren:** Public Domain

Jeder kann kompatible Tools bauen, ohne Lizenzgebühren oder Genehmigungen.

---

## 📚 Referenzen

- [AGE Encryption](https://age-encryption.org/v1)
- [BLAKE3 Specification](https://github.com/BLAKE3-team/BLAKE3/blob/master/spec/blake3.pdf)
- [ZSTD Format](https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md)
- [FastCDC Paper](https://www.usenix.org/system/files/conference/atc16/atc16-paper-xia.pdf)
- [Merkle Trees](https://en.wikipedia.org/wiki/Merkle_tree)

---

**Dokument-Version:** 1.0  
**Letzte Aktualisierung:** 2025-01-15  
**Kontakt:** spec@omnibackup.dev
