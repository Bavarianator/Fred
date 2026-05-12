// src/core/compression.rs - Adaptive ZSTD Compression
use anyhow::Result;
use zstd::stream::{decode_all, encode_all};

/// Adaptive compression based on content type and size
pub struct Compressor {
    level: i32,
}

impl Compressor {
    pub fn new(level: i32) -> Self {
        let clamped = level.clamp(-7, 22);
        Self { level: clamped }
    }

    pub fn auto_level(data: &[u8]) -> i32 {
        if data.len() < 4096 {
            3
        } else {
            let entropy = Self::estimate_entropy(data);
            if entropy > 7.5 {
                0
            } else if entropy > 6.0 {
                3
            } else {
                15
            }
        }
    }

    fn estimate_entropy(data: &[u8]) -> f64 {
        let mut histogram = [0usize; 256];
        for &byte in data {
            histogram[byte as usize] += 1;
        }
        
        let len = data.len() as f64;
        let mut entropy = 0.0;
        
        for &count in &histogram {
            if count > 0 {
                let p = count as f64 / len;
                entropy -= p * p.log2();
            }
        }
        
        entropy
    }

    pub fn compress(&self, data: &[u8]) -> Result<Vec<u8>> {
        encode_all(data, self.level)
            .map_err(|e| anyhow::anyhow!("ZSTD compression failed: {}", e))
    }

    pub fn decompress(&self, data: &[u8]) -> Result<Vec<u8>> {
        decode_all(data)
            .map_err(|e| anyhow::anyhow!("ZSTD decompression failed: {}", e))
    }

    pub fn estimate_ratio(&self, data: &[u8]) -> f64 {
        match self.compress(data) {
            Ok(compressed) => compressed.len() as f64 / data.len() as f64,
            Err(_) => 1.0,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compress_decompress() {
        let compressor = Compressor::new(9);
        let original = b"Hello World! This is a test of ZSTD compression.";
        
        let compressed = compressor.compress(original).unwrap();
        let decompressed = compressor.decompress(&compressed).unwrap();
        
        assert_eq!(original.to_vec(), decompressed);
        assert!(compressed.len() < original.len());
    }
}
