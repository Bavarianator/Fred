// src/core/stats.rs - Backup Statistics & Analytics
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupStats {
    pub total_backups: usize,
    pub successful_backups: usize,
    pub failed_backups: usize,
    pub total_files: u64,
    pub total_size: u64,
    pub compressed_size: u64,
    pub deduplicated_size: u64,
    pub compression_ratio: f64,
    pub dedup_ratio: f64,
    pub avg_backup_time_secs: f64,
    pub last_backup: Option<i64>,
    pub next_scheduled: Option<i64>,
}

impl BackupStats {
    pub fn new() -> Self {
        Self {
            total_backups: 0,
            successful_backups: 0,
            failed_backups: 0,
            total_files: 0,
            total_size: 0,
            compressed_size: 0,
            deduplicated_size: 0,
            compression_ratio: 1.0,
            dedup_ratio: 1.0,
            avg_backup_time_secs: 0.0,
            last_backup: None,
            next_scheduled: None,
        }
    }

    pub fn overall_savings(&self) -> u64 {
        self.total_size.saturating_sub(self.deduplicated_size)
    }

    pub fn savings_percentage(&self) -> f64 {
        if self.total_size == 0 {
            return 0.0;
        }
        1.0 - (self.deduplicated_size as f64 / self.total_size as f64)
    }
}

impl Default for BackupStats {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub struct LiveProgress {
    pub current_file: String,
    pub files_processed: u64,
    pub bytes_processed: u64,
    pub total_bytes: u64,
    pub chunks_created: u64,
    pub chunks_deduplicated: u64,
    pub speed_mbps: f64,
    pub eta_secs: Option<u64>,
    pub phase: BackupPhase,
}

#[derive(Debug, Clone, PartialEq)]
pub enum BackupPhase {
    Scanning,
    Chunking,
    Compressing,
    Encrypting,
    Uploading,
    Verifying,
    Complete,
}

impl LiveProgress {
    pub fn progress_percent(&self) -> f64 {
        if self.total_bytes == 0 {
            return 0.0;
        }
        (self.bytes_processed as f64 / self.total_bytes as f64) * 100.0
    }
}
