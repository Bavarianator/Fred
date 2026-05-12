//! Error-Handling mit thiserror

use thiserror::Error;

/// Haupt-Error-Typ für OmniBackup
#[derive(Error, Debug)]
pub enum OmniError {
    /// IO-Fehler
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    /// TOML-Parsing-Fehler
    #[error("Config parsing error: {0}")]
    Toml(#[from] toml::de::Error),
    
    /// JSON-Parsing-Fehler
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    /// Age-Verschlüsselungsfehler
    #[error("Encryption error: {0}")]
    Age(#[from] age::Error),
    
    /// Argon2-Passwort-Hashing-Fehler
    #[error("Password hashing error: {0}")]
    Argon2(#[from] argon2::password_hash::Error),
    
    /// ChaCha20-Poly1305-Fehler
    #[error("AEAD error: {0}")]
    Aead(#[from] chacha20poly1305::Error),
    
    /// BLAKE3-Hashing-Fehler
    #[error("Hashing error: {0}")]
    Blake3(#[from] blake3::Error),
    
    /// ZSTD-Kompressionsfehler
    #[error("Compression error: {0}")]
    Zstd(#[from] zstd::stream::ReadError),
    
    /// SQLite-Datenbankfehler
    #[error("Database error: {0}")]
    Sqlx(#[from] sqlx::Error),
    
    /// OpenDAL-Storage-Fehler
    #[error("Storage error: {0}")]
    OpenDal(#[from] opendal::Error),
    
    /// LibP2P-Netzwerkfehler
    #[error("P2P error: {0}")]
    LibP2P(#[from] libp2p::swarm::ConnectionError),
    
    /// Chrono-Zeitfehler
    #[error("Time error: {0}")]
    Chrono(#[from] chrono::ParseError),
    
    /// HKDF-Key-Derivation-Fehler
    #[error("Key derivation error: {0}")]
    Hkdf(#[from] hkdf::InvalidInfoLength),
    
    /// Allgemeiner Fehler mit Nachricht
    #[error("{0}")]
    Message(String),
}

impl From<&str> for OmniError {
    fn from(msg: &str) -> Self {
        OmniError::Message(msg.to_string())
    }
}

impl From<String> for OmniError {
    fn from(msg: String) -> Self {
        OmniError::Message(msg)
    }
}

/// Result-Type Alias
pub type Result<T> = std::result::Result<T, OmniError>;
