// src/core/backup.rs - Core Backup Engine
use anyhow::Result;
use std::path::{Path, PathBuf};
use tokio::fs;
use crate::core::{chunker::Chunker, compression::Compressor, crypto::CryptoEngine, dedup::DedupIndex};

pub struct BackupEngine {
    chunker: Chunker,
    compressor: Compressor,
    crypto: CryptoEngine,
    dedup_index: DedupIndex,
}

impl BackupEngine {
    pub fn new(passphrase: &str) -> Result<Self> {
        Ok(Self {
            chunker: Chunker::new(),
            compressor: Compressor::new(9),
            crypto: CryptoEngine::new(passphrase)?,
            dedup_index: DedupIndex::new(),
        })
    }

    pub async fn backup_file(&mut self, path: &Path) -> Result<BackupResult> {
        let mut result = BackupResult::default();
        
        // Read file
        let data = fs::read(path).await?;
        result.original_size = data.len() as u64;
        
        // Chunk file
        let chunks = self.chunker.chunk(&data);
        result.chunks_created = chunks.len();
        
        // Process each chunk
        for chunk in chunks {
            // Check for duplicate
            if self.dedup_index.add_chunk(&chunk, "") {
                result.chunks_deduplicated += 1;
                continue;
            }
            
            // Compress
            let compressed = self.compressor.compress(&chunk)?;
            
            // Encrypt
            let encrypted = self.crypto.encrypt(&compressed)?;
            
            result.processed_chunks += 1;
            result.compressed_size += compressed.len() as u64;
            result.encrypted_size += encrypted.len() as u64;
        }
        
        Ok(result)
    }

    pub async fn restore_file(&self, _chunk_ids: &[String], _target: &Path) -> Result<Vec<u8>> {
        // TODO: Implement restore logic
        Ok(Vec::new())
    }

    pub fn get_dedup_stats(&self) -> crate::core::dedup::DedupStats {
        self.dedup_index.stats()
    }
}

#[derive(Debug, Default)]
pub struct BackupResult {
    pub original_size: u64,
    pub compressed_size: u64,
    pub encrypted_size: u64,
    pub chunks_created: usize,
    pub processed_chunks: usize,
    pub chunks_deduplicated: usize,
}

impl BackupResult {
    pub fn compression_ratio(&self) -> f64 {
        if self.original_size == 0 {
            return 1.0;
        }
        self.compressed_size as f64 / self.original_size as f64
    }

    pub fn dedup_savings(&self) -> f64 {
        if self.chunks_created == 0 {
            return 0.0;
        }
        (self.chunks_deduplicated as f64 / self.chunks_created as f64) * 100.0
    }
}
