// src/core/repository.rs - Repository Format & Management
use anyhow::Result;
use std::path::{Path, PathBuf};
use std::fs;
use serde::{Serialize, Deserialize};

/// Repository metadata structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryConfig {
    pub version: String,
    pub format_spec: String,
    pub created_at: i64,
    pub encryption: EncryptionConfig,
    pub compression: CompressionConfig,
    pub chunking: ChunkingConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptionConfig {
    pub algorithm: String,
    pub kdf: String,
    pub key_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressionConfig {
    pub algorithm: String,
    pub level: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkingConfig {
    pub algorithm: String,
    pub min_size: usize,
    pub avg_size: usize,
    pub max_size: usize,
}

/// Repository manager
pub struct Repository {
    pub path: PathBuf,
    pub config: RepositoryConfig,
}

impl Repository {
    /// Create or open a repository
    pub fn open(path: &Path) -> Result<Self> {
        let config_path = path.join("omnibackup.toml");
        
        if !config_path.exists() {
            // Create new repository
            Self::create(path)
        } else {
            // Open existing repository
            let config_str = fs::read_to_string(&config_path)?;
            let config: RepositoryConfig = toml::from_str(&config_str)?;
            
            Ok(Self {
                path: path.to_path_buf(),
                config,
            })
        }
    }

    /// Create a new repository with default configuration
    pub fn create(path: &Path) -> Result<Self> {
        // Create directory structure
        fs::create_dir_all(path.join("chunks"))?;
        fs::create_dir_all(path.join("snapshots"))?;
        fs::create_dir_all(path.join("index"))?;
        fs::create_dir_all(path.join("keys"))?;

        let config = RepositoryConfig {
            version: "1.0.0".to_string(),
            format_spec: "https://omnibackup.io/format-spec/v1.0".to_string(),
            created_at: chrono::Utc::now().timestamp(),
            encryption: EncryptionConfig {
                algorithm: "age-X25519-ChaCha20-Poly1305".to_string(),
                kdf: "Argon2id".to_string(),
                key_id: uuid::Uuid::new_v4().to_string(),
            },
            compression: CompressionConfig {
                algorithm: "zstd".to_string(),
                level: 9,
            },
            chunking: ChunkingConfig {
                algorithm: "FastCDC".to_string(),
                min_size: 256 * 1024,      // 256 KB
                avg_size: 1024 * 1024,     // 1 MB
                max_size: 4 * 1024 * 1024, // 4 MB
            },
        };

        // Write config
        let config_str = toml::to_string_pretty(&config)?;
        fs::write(path.join("omnibackup.toml"), &config_str)?;

        // Write recovery instructions
        Self::write_recovery_instructions(path)?;

        Ok(Self {
            path: path.to_path_buf(),
            config,
        })
    }

    fn write_recovery_instructions(path: &Path) -> Result<()> {
        let content = r#"# OmniBackup Recovery Instructions
# ====================================

This backup repository uses the OmniBackup Format Specification v1.0.
You can recover your data even without the OmniBackup software using standard tools.

## Requirements
- age (https://age-encryption.org/)
- zstd (https://facebook.github.io/zstd/)
- blake3 (https://github.com/BLAKE3-team/BLAKE3)

## Recovery Steps

1. Locate your encrypted master key:
   cp keys/master.age ./recovery-key.age

2. Decrypt the master key (you need your passphrase):
   age --decrypt --output master.key --passphrase recovery-key.age

3. List available snapshots:
   ls snapshots/

4. Decrypt a snapshot manifest:
   age --decrypt --input master.key snapshots/2025-01-15_142300.json.age > manifest.json

5. The manifest contains file paths and chunk IDs. Retrieve chunks:
   # Chunks are stored as: chunks/XX/XXXX...blake3.zst.age
   # Example for chunk ab3f...:
   age --decrypt --input master.key chunks/ab/ab3f....zst.age | zstd -d > recovered_chunk

6. Verify integrity with BLAKE3:
   blake3sum recovered_chunk

## For More Help
Visit: https://omnibackup.io/recovery
"#;
        fs::write(path.join("RECOVERY.txt"), content)?;
        Ok(())
    }

    /// Get chunk storage path from chunk ID
    pub fn get_chunk_path(&self, chunk_id: &str) -> PathBuf {
        let prefix = &chunk_id[0..2];
        self.path.join("chunks").join(prefix).join(format!("{}.zst.age", chunk_id))
    }

    /// Get snapshot path
    pub fn get_snapshot_path(&self, snapshot_id: &str) -> PathBuf {
        self.path.join("snapshots").join(format!("{}.json.age", snapshot_id))
    }

    /// Get index database path
    pub fn get_index_path(&self) -> PathBuf {
        self.path.join("index").join("snapshots.db")
    }

    /// Verify repository integrity
    pub fn verify(&self) -> Result<VerificationReport> {
        let mut report = VerificationReport {
            config_valid: false,
            chunks_found: 0,
            snapshots_found: 0,
            errors: Vec::new(),
        };

        // Check config
        if self.config.version.starts_with("1.") {
            report.config_valid = true;
        } else {
            report.errors.push("Unsupported repository version".to_string());
        }

        // Count chunks
        let chunks_dir = self.path.join("chunks");
        if chunks_dir.exists() {
            for entry in fs::read_dir(&chunks_dir)? {
                if let Ok(entry) = entry {
                    if entry.path().is_dir() {
                        if let Ok(sub_entries) = fs::read_dir(entry.path()) {
                            report.chunks_found += sub_entries.count();
                        }
                    }
                }
            }
        }

        // Count snapshots
        let snapshots_dir = self.path.join("snapshots");
        if snapshots_dir.exists() {
            report.snapshots_found = fs::read_dir(&snapshots_dir)?
                .filter_map(|e| e.ok())
                .filter(|e| e.path().extension().map_or(false, |ext| ext == "age"))
                .count();
        }

        Ok(report)
    }
}

#[derive(Debug)]
pub struct VerificationReport {
    pub config_valid: bool,
    pub chunks_found: usize,
    pub snapshots_found: usize,
    pub errors: Vec<String>,
}
