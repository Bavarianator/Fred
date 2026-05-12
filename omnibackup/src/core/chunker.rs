//! FastCDC Content-Defined Chunking
//! 
//! Implementiert den FastCDC-Algorithmus für intelligente Datenteilung.

use anyhow::Result;
use bytes::Bytes;
use crate::core::Chunk;

/// FastCDC Chunker Konfiguration
#[derive(Debug, Clone)]
pub struct ChunkerConfig {
    /// Minimale Chunk-Größe (default: 256 KB)
    pub min_size: usize,
    /// Durchschnittliche Chunk-Größe (default: 1 MB)
    pub avg_size: usize,
    /// Maximale Chunk-Größe (default: 4 MB)
    pub max_size: usize,
}

impl Default for ChunkerConfig {
    fn default() -> Self {
        Self {
            min_size: 256 * 1024,      // 256 KB
            avg_size: 1024 * 1024,     // 1 MB
            max_size: 4 * 1024 * 1024, // 4 MB
        }
    }
}

/// FastCDC Chunker
pub struct FastCDC {
    config: ChunkerConfig,
    /// Rolling Hash State
    hash_state: u64,
}

impl FastCDC {
    /// Neuen Chunker erstellen
    pub fn new(config: ChunkerConfig) -> Self {
        Self {
            config,
            hash_state: 0,
        }
    }
    
    /// Daten in Chunks teilen
    /// 
    /// # Arguments
    /// * `data` - Eingabedaten
    /// * `offset` - Start-Offset im Originalstream
    /// 
    /// # Returns
    /// Vector von Chunks mit BLAKE3-Hashes
    pub fn chunk(&mut self, data: &[u8], offset: u64) -> Result<Vec<Chunk>> {
        let mut chunks = Vec::new();
        let mut pos = 0;
        let mut current_offset = offset;
        
        while pos < data.len() {
            // Nächste Cut-Position finden
            let cut_pos = self.find_cut_point(data, pos)?;
            
            // Chunk-Daten extrahieren
            let chunk_data = &data[pos..cut_pos];
            
            // BLAKE3-Hash berechnen
            let hash = blake3::hash(chunk_data).to_hex().to_string();
            
            let chunk = Chunk {
                hash,
                offset: current_offset,
                size: chunk_data.len(),
                compressed_size: None, // Wird später gesetzt
            };
            
            chunks.push(chunk);
            
            // Positionen aktualisieren
            current_offset += chunk_data.len() as u64;
            pos = cut_pos;
        }
        
        Ok(chunks)
    }
    
    /// Finde nächste Cut-Position mittels FastCDC-Algorithmus
    fn find_cut_point(&mut self, data: &[u8], start: usize) -> Result<usize> {
        let mut pos = start + self.config.min_size;
        
        // Wenn weniger als min_size übrig, gesamten Rest nehmen
        if pos >= data.len() {
            return Ok(data.len());
        }
        
        // Rolling Hash initialisieren
        self.hash_state = 0;
        
        // Hash über min_size Bytes berechnen
        for &byte in &data[start..pos] {
            self.hash_state = self.roll_hash(self.hash_state, byte);
        }
        
        // Nach Cut-Point suchen
        while pos < data.len() && pos < start + self.config.max_size {
            // Hash updaten
            self.hash_state = self.roll_hash(self.hash_state, data[pos]);
            
            // Check ob wir einen Cut-Point haben
            // FastCDC: Check ob untere N Bits des Hashes 0 sind
            if self.is_cut_point(self.hash_state) {
                return Ok(pos + 1);
            }
            
            pos += 1;
        }
        
        // Maximalgröße erreicht, hier cutten
        Ok(pos.min(data.len()))
    }
    
    /// Rolling Hash Update (Gear Hash)
    fn roll_hash(&self, state: u64, byte: u8) -> u64 {
        // Gear Hash: (state << 1) ^ gear_table[byte]
        const GEAR_TABLE: [u64; 256] = generate_gear_table();
        ((state << 1) ^ GEAR_TABLE[byte as usize]).wrapping_mul(0x5DEECE66D).wrapping_add(0xB)
    }
    
    /// Check ob aktuelle Position ein Cut-Point ist
    fn is_cut_point(&self, hash: u64) -> bool {
        // FastCDC: Check ob untere 12-16 Bits 0 sind
        // Je mehr Bits, desto größer die Chunks
        let mask = (1 << 14) - 1; // 14 Bits = ~16KB average bei random data
        (hash & mask) == 0
    }
    
    /// Stream-Chunking für große Dateien
    pub async fn chunk_stream<S>(
        &mut self,
        mut stream: S,
    ) -> Result<Vec<Chunk>>
    where
        S: tokio::io::AsyncRead + Unpin,
    {
        use tokio::io::AsyncReadExt;
        
        let mut chunks = Vec::new();
        let mut buffer = vec![0u8; self.config.max_size];
        let mut offset = 0u64;
        
        loop {
            let n = stream.read(&mut buffer).await?;
            if n == 0 {
                break;
            }
            
            let stream_chunks = self.chunk(&buffer[..n], offset)?;
            offset += n as u64;
            chunks.extend(stream_chunks);
        }
        
        Ok(chunks)
    }
}

/// Gear Table für FastCDC (deterministisch generiert)
const fn generate_gear_table() -> [u64; 256] {
    let mut table = [0u64; 256];
    let mut i = 0;
    while i < 256 {
        // Einfache Pseudo-Zufallszahlen für Compile-Time-Konstanz
        table[i] = ((i as u64 * 7919 + 104729) % (1 << 32)) as u64;
        i += 1;
    }
    table
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_chunking_basic() {
        let mut chunker = FastCDC::new(ChunkerConfig::default());
        let data = b"Hello World! This is a test file for chunking.";
        
        let chunks = chunker.chunk(data, 0).unwrap();
        
        assert!(!chunks.is_empty());
        assert!(chunks.iter().all(|c| c.size > 0));
        
        // Alle Chunks sollten zusammen die Originalgröße ergeben
        let total_size: usize = chunks.iter().map(|c| c.size).sum();
        assert_eq!(total_size, data.len());
    }
    
    #[test]
    fn test_chunking_deterministic() {
        let data = vec![0u8; 1024 * 1024]; // 1 MB
        
        let mut chunker1 = FastCDC::new(ChunkerConfig::default());
        let chunks1 = chunker1.chunk(&data, 0).unwrap();
        
        let mut chunker2 = FastCDC::new(ChunkerConfig::default());
        let chunks2 = chunker2.chunk(&data, 0).unwrap();
        
        // Gleiche Daten sollten gleiche Chunks produzieren
        assert_eq!(chunks1.len(), chunks2.len());
        for (c1, c2) in chunks1.iter().zip(chunks2.iter()) {
            assert_eq!(c1.hash, c2.hash);
            assert_eq!(c1.size, c2.size);
        }
    }
}
