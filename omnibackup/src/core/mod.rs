//! Core-Module für Backup-Logik

pub mod chunker;
pub mod crypto;
pub mod compression;
pub mod dedup;
pub mod merkle;
pub mod repository;
pub mod snapshot;
pub mod index;
pub mod backup;
pub mod stats;
pub mod gc;
pub mod optimize;
pub mod migrate;

use anyhow::Result;
use serde::{Deserialize, Serialize};

/// Chunk-Information nach FastCDC
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    /// BLAKE3-Hash des Chunks
    pub hash: String,
    /// Offset in der Originaldatei
    pub offset: u64,
    /// Unkomprimierte Größe
    pub size: usize,
    /// Komprimierte Größe (nach ZSTD)
    pub compressed_size: Option<usize>,
}

/// Datei-Metadaten
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    /// Vollständiger Pfad
    pub path: String,
    /// Typ: file, directory, symlink
    pub r#type: String,
    /// Dateigröße in Bytes
    pub size: u64,
    /// Unix-Modus (z.B. "0644")
    pub mode: String,
    /// User-ID
    pub uid: u32,
    /// Group-ID
    pub gid: u32,
    /// Modification Time
    pub mtime: chrono::DateTime<chrono::Utc>,
    /// Access Time
    pub atime: Option<chrono::DateTime<chrono::Utc>>,
    /// Change Time
    pub ctime: Option<chrono::DateTime<chrono::Utc>>,
    /// BLAKE3-Hash der gesamten Datei
    pub hash: Option<String>,
    /// Chunk-Liste
    pub chunks: Vec<Chunk>,
    /// Symlink-Ziel falls zutreffend
    pub symlink_target: Option<String>,
    /// Extended Attributes
    pub xattrs: std::collections::HashMap<String, String>,
}

/// Snapshot-Metadaten
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    /// Eindeutige Snapshot-ID
    pub snapshot_id: String,
    /// Erstellungszeitpunkt
    pub created_at: chrono::DateTime<chrono::Utc>,
    /// Hostname
    pub hostname: String,
    /// Username
    pub username: String,
    /// Betriebssystem
    pub os: String,
    /// OmniBackup-Version
    pub omnibackup_version: String,
    /// Quellen-Liste
    pub sources: Vec<SourceInfo>,
    /// Dateien (nur im verschlüsselten Manifest)
    pub files: Vec<FileMetadata>,
    /// Statistiken
    pub stats: SnapshotStats,
    /// Tags
    pub tags: Vec<String>,
    /// Notizen
    pub notes: String,
    /// Merkle-Root-Hash
    pub merkle_root: String,
}

/// Quellen-Information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceInfo {
    /// Pfad
    pub path: String,
    /// Typ: directory, file, database, etc.
    pub r#type: String,
    /// Anzahl Dateien
    pub total_files: usize,
    /// Gesamte Byte-Anzahl
    pub total_bytes: u64,
    /// Anzahl Chunks
    pub chunk_count: usize,
}

/// Snapshot-Statistiken
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotStats {
    /// Gesamtanzahl Dateien
    pub total_files: usize,
    /// Gesamtanzahl Verzeichnisse
    pub total_dirs: usize,
    /// Gesamtanzahl Symlinks
    pub total_symlinks: usize,
    /// Gesamte Byte-Anzahl
    pub total_bytes: u64,
    /// Einzigartige Chunks
    pub unique_chunks: usize,
    /// Deduplizierte Chunks
    pub deduplicated_chunks: usize,
    /// Dedup-Ratio (0.0-1.0)
    pub dedup_ratio: f64,
    /// Komprimierte Größe
    pub compressed_size: u64,
    /// Kompressions-Ratio
    pub compression_ratio: f64,
    /// Dauer in Sekunden
    pub duration_seconds: u64,
    /// Durchsatz in MB/s
    pub throughput_mbps: f64,
}

impl Snapshot {
    /// Neuen Snapshot erstellen
    pub fn new(hostname: String, username: String) -> Self {
        Self {
            snapshot_id: uuid::Uuid::new_v4().to_string(),
            created_at: chrono::Utc::now(),
            hostname,
            username,
            os: std::env::consts::OS.to_string(),
            omnibackup_version: env!("CARGO_PKG_VERSION").to_string(),
            sources: Vec::new(),
            files: Vec::new(),
            stats: SnapshotStats {
                total_files: 0,
                total_dirs: 0,
                total_symlinks: 0,
                total_bytes: 0,
                unique_chunks: 0,
                deduplicated_chunks: 0,
                dedup_ratio: 0.0,
                compressed_size: 0,
                compression_ratio: 0.0,
                duration_seconds: 0,
                throughput_mbps: 0.0,
            },
            tags: Vec::new(),
            notes: String::new(),
            merkle_root: String::new(),
        }
    }
}
