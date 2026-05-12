// src/core/dedup.rs - BLAKE3-based Deduplication
use anyhow::Result;
use blake3::Hasher;
use std::collections::{HashMap, HashSet};

/// Chunk fingerprint for deduplication
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ChunkId(pub String);

impl ChunkId {
    pub fn from_data(data: &[u8]) -> Self {
        let hash = blake3::hash(data);
        ChunkId(hash.to_hex().to_string())
    }
    
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Deduplication index tracking all known chunks
pub struct DedupIndex {
    chunks: HashMap<ChunkId, ChunkInfo>,
    total_size: u64,
    stored_size: u64,
}

#[derive(Debug, Clone)]
pub struct ChunkInfo {
    pub size: usize,
    pub ref_count: u32,
    pub storage_path: String,
}

impl DedupIndex {
    pub fn new() -> Self {
        Self {
            chunks: HashMap::new(),
            total_size: 0,
            stored_size: 0,
        }
    }

    /// Check if chunk exists and increment ref count
    pub fn add_chunk(&mut self, data: &[u8], storage_path: &str) -> bool {
        let chunk_id = ChunkId::from_data(data);
        let size = data.len();
        
        self.total_size += size as u64;
        
        if let Some(info) = self.chunks.get_mut(&chunk_id) {
            info.ref_count += 1;
            true // Duplicate found
        } else {
            self.stored_size += size as u64;
            self.chunks.insert(chunk_id, ChunkInfo {
                size,
                ref_count: 1,
                storage_path: storage_path.to_string(),
            });
            false // New chunk
        }
    }

    /// Get storage path for a chunk
    pub fn get_chunk_path(&self, data: &[u8]) -> Option<String> {
        let chunk_id = ChunkId::from_data(data);
        self.chunks.get(&chunk_id).map(|info| info.storage_path.clone())
    }

    /// Decrement reference count
    pub fn remove_reference(&mut self, data: &[u8]) -> bool {
        let chunk_id = ChunkId::from_data(data);
        
        if let Some(info) = self.chunks.get_mut(&chunk_id) {
            info.ref_count -= 1;
            if info.ref_count == 0 {
                self.stored_size -= info.size as u64;
                self.chunks.remove(&chunk_id);
            }
            true
        } else {
            false
        }
    }

    /// Get deduplication statistics
    pub fn stats(&self) -> DedupStats {
        let saved = self.total_size.saturating_sub(self.stored_size);
        let ratio = if self.total_size > 0 {
            self.stored_size as f64 / self.total_size as f64
        } else {
            1.0
        };
        
        DedupStats {
            total_chunks: self.chunks.len(),
            total_size: self.total_size,
            stored_size: self.stored_size,
            saved_size: saved,
            ratio,
        }
    }

    /// Find orphaned chunks (ref_count == 0)
    pub fn find_orphans(&self) -> Vec<ChunkId> {
        self.chunks
            .iter()
            .filter(|(_, info)| info.ref_count == 0)
            .map(|(id, _)| id.clone())
            .collect()
    }
}

#[derive(Debug)]
pub struct DedupStats {
    pub total_chunks: usize,
    pub total_size: u64,
    pub stored_size: u64,
    pub saved_size: u64,
    pub ratio: f64,
}

impl Default for DedupIndex {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dedup_detection() {
        let mut index = DedupIndex::new();
        let data = b"Hello World";
        
        // First add
        assert!(!index.add_chunk(data, "/chunks/ab/abc123"));
        
        // Duplicate add
        assert!(index.add_chunk(data, "/chunks/ab/abc123"));
        
        let stats = index.stats();
        assert_eq!(stats.total_chunks, 1);
        assert_eq!(stats.ref_count, 2);
        assert!(stats.ratio < 1.0);
    }

    #[test]
    fn test_chunk_id_generation() {
        let data = b"Test data";
        let id1 = ChunkId::from_data(data);
        let id2 = ChunkId::from_data(data);
        let id3 = ChunkId::from_data(b"Different data");
        
        assert_eq!(id1, id2);
        assert_ne!(id1, id3);
    }
}
