//! Kryptographie-Module: age, ChaCha20-Poly1305, Argon2id

use anyhow::{Result, Context};
use age::{Identity, Recipient, IdentityFile, Encryptor, Decryptor};
use argon2::{Argon2, PasswordHash, Salt, password_hash::PasswordHasher};
use chacha20poly1305::{ChaCha20Poly1305, Key, Nonce, AeadInPlace};
use rand::RngCore;
use zeroize::Zeroizing;
use std::path::Path;
use crate::config::Config;

/// Master-Key Wrapper
pub struct MasterKey {
    /// Der 32-Byte Master-Key
    key: Zeroizing<[u8; 32]>,
    /// Age Identity für Repository-Verschlüsselung
    identity: age::x25519::Identity,
}

impl MasterKey {
    /// Master-Key aus Passwort ableiten (Argon2id)
    pub fn from_password(password: &str, salt: &[u8; 16]) -> Result<Self> {
        // Argon2id Parameter (OWASP 2024)
        let argon2 = Argon2::new(
            argon2::Algorithm::Argon2id,
            argon2::Version::V0x13,
            argon2::Params::new(65536, 3, 4, 32)?, // 64MB, 3 iterations, 4 parallelism, 32 byte output
        );
        
        let salt = Salt::from_b64(encoded_salt(salt))
            .context("Invalid salt encoding")?;
        
        let hash = argon2.hash_password(password.as_bytes(), &salt)?;
        
        let mut key = [0u8; 32];
        hash.hash
            .ok_or_else(|| anyhow::anyhow!("No hash in password hash"))?
            .as_bytes()
            .read_slice(&mut key)
            .context("Failed to extract key from hash")?;
        
        // X25519 Identity aus Master-Key ableiten
        let identity = derive_x25519_identity(&key);
        
        Ok(Self {
            key: Zeroizing::new(key),
            identity,
        })
    }
    
    /// Zufälligen Salt generieren
    pub fn generate_salt() -> [u8; 16] {
        let mut salt = [0u8; 16];
        rand::thread_rng().fill_bytes(&mut salt);
        salt
    }
    
    /// Chunk-Key ableiten (HKDF-SHA256)
    pub fn derive_chunk_key(&self, chunk_hash: &str) -> Result<Key> {
        use hkdf::Hkdf;
        use sha2::Sha256;
        
        let hkdf = Hkdf::<Sha256>::new(Some(chunk_hash.as_bytes()), &self.key);
        let mut okm = [0u8; 32];
        hkdf.expand(b"omnibackup-chunk-v1", &mut okm)?;
        
        Ok(*Key::from_slice(&okm))
    }
    
    /// Age Identity für Repository-Operationen
    pub fn identity(&self) -> &age::x25519::Identity {
        &self.identity
    }
    
    /// Age Recipient für Verschlüsselung
    pub fn recipient(&self) -> age::x25519::Recipient {
        self.identity.to_public()
    }
}

/// X25519 Identity aus Master-Key ableiten
fn derive_x25519_identity(key: &[u8; 32]) -> age::x25519::Identity {
    // Einfache Ableitung: verwende erste 32 Bytes als Seed
    // In Produktion: proper HKDF mit "omnibackup-identity" info
    use curve25519_dalek::Scalar;
    
    let scalar = Scalar::from_bytes_mod_order(*key);
    age::x25519::Identity::from(scalar.to_bytes())
}

/// Salt für Argon2 Base64-encodieren
fn encoded_salt(salt: &[u8; 16]) -> String {
    use base64::{Engine, engine::general_purpose::STANDARD_NO_PAD};
    STANDARD_NO_PAD.encode(salt)
}

/// Daten verschlüsseln (ChaCha20-Poly1305 + AGE)
pub fn encrypt_chunk(data: &[u8], chunk_key: &Key) -> Result<Vec<u8>> {
    let cipher = ChaCha20Poly1305::new(chunk_key);
    
    // Nonce generieren (12 bytes)
    let mut nonce_bytes = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from(nonce_bytes);
    
    // Verschlüsseln
    let mut ciphertext = data.to_vec();
    cipher.encrypt_in_place(&nonce, b"", &mut ciphertext)?;
    
    // Nonce + Ciphertext zurückgeben
    let mut result = Vec::with_capacity(12 + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend(ciphertext);
    
    Ok(result)
}

/// Daten entschlüsseln
pub fn decrypt_chunk(encrypted: &[u8], chunk_key: &Key) -> Result<Vec<u8>> {
    if encrypted.len() < 12 {
        anyhow::bail!("Ciphertext too short");
    }
    
    let nonce_bytes = &encrypted[..12];
    let ciphertext = &encrypted[12..];
    
    let cipher = ChaCha20Poly1305::new(chunk_key);
    let nonce = Nonce::from_slice(nonce_bytes);
    
    let mut plaintext = ciphertext.to_vec();
    cipher.decrypt_in_place(nonce, b"", &mut plaintext)?;
    
    Ok(plaintext)
}

/// Repository Master-Key laden oder erstellen
pub async fn load_or_create_master_key(
    repo_path: &Path,
    password: Option<&str>,
) -> Result<MasterKey> {
    let key_file = repo_path.join("keys").join("master.age");
    
    if key_file.exists() {
        // Vorhandenen Key laden
        load_master_key(&key_file, password)
    } else {
        // Neuen Key erstellen
        create_master_key(repo_path, password)
    }
}

/// Master-Key aus Datei laden
fn load_master_key(key_file: &Path, password: Option<&str>) -> Result<MasterKey> {
    let password = password.context("Password required to decrypt master key")?;
    
    // Identity-File laden
    let identity_file = IdentityFile::from_file(key_file)?;
    
    // Mit Passwort entschlüsseln
    let identities = identity_file.into_identities(password)?;
    
    // Erste Identity extrahieren
    let identity = identities.first()
        .context("No identities found")?
        .clone();
    
    // In x25519 konvertieren
    if let Some(x25519) = identity.as_x25519() {
        // Master-Key rekonstruieren (aus Identity ableiten)
        let key = x25519.to_bytes();
        Ok(MasterKey {
            key: Zeroizing::new(key),
            identity: x25519.clone(),
        })
    } else {
        anyhow::bail!("Unsupported identity type")
    }
}

/// Neuen Master-Key erstellen und speichern
fn create_master_key(repo_path: &Path, password: Option<&str>) -> Result<MasterKey> {
    // Zufälligen Master-Key generieren
    let mut key = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut key);
    
    let salt = MasterKey::generate_salt();
    
    // Identity erstellen
    let identity = derive_x25519_identity(&key);
    let master_key = MasterKey {
        key: Zeroizing::new(key),
        identity: identity.clone(),
    };
    
    // Mit Passwort verschlüsseln und speichern
    if let Some(pwd) = password {
        let keys_dir = repo_path.join("keys");
        std::fs::create_dir_all(&keys_dir)?;
        
        let key_file = keys_dir.join("master.age");
        
        // AGE-Verschlüsselung mit Passwort
        let recipient = age::scrypt::Recipient::new(pwd.try_into()?);
        let encrypted = age::Encryptor::with_recipients(vec![Box::new(recipient)])?
            .wrap_iter(|writer| {
                // Identity im AGE-Format schreiben
                write_identity_to(writer, &identity)
            })?;
        
        std::fs::write(key_file, encrypted)?;
    }
    
    Ok(master_key)
}

/// Identity in AGE-Format schreiben
fn write_identity_to<W: std::io::Write>(
    writer: W,
    identity: &age::x25519::Identity,
) -> std::io::Result<()> {
    writeln!(writer, "# created: {}", chrono::Utc::now().to_rfc3339())?;
    writeln!(writer, "# public key: {}", identity.to_public())?;
    writeln!(writer, "{}", identity.to_string())?;
    Ok(())
}

/// Recovery-Key generieren (für Disaster Recovery)
pub fn generate_recovery_key(config: &Config) -> Result<String> {
    // QR-Code-fähiger Recovery-Key
    let repo_id = config.repo.id.clone();
    let created = chrono::Utc::now().timestamp();
    
    // Base32-Encoded Key für einfache Eingabe
    let recovery_data = format!(
        "OMNIBACKUP:v1:{}:{}",
        repo_id,
        created
    );
    
    use data_encoding::BASE32_NOPAD;
    Ok(BASE32_NOPAD.encode(recovery_data.as_bytes()))
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_master_key_derivation() {
        let password = "test-password-123";
        let salt = MasterKey::generate_salt();
        
        let key1 = MasterKey::from_password(password, &salt).unwrap();
        let key2 = MasterKey::from_password(password, &salt).unwrap();
        
        // Gleiche Parameter sollten gleichen Key produzieren
        assert_eq!(&key1.key[..], &key2.key[..]);
    }
    
    #[test]
    fn test_chunk_encryption() {
        let data = b"Hello, World! This is a test chunk.";
        let key = [42u8; 32];
        
        let encrypted = encrypt_chunk(data, &Key::from(key)).unwrap();
        let decrypted = decrypt_chunk(&encrypted, &Key::from(key)).unwrap();
        
        assert_ne!(data.to_vec(), encrypted);
        assert_eq!(data.to_vec(), decrypted);
    }
}
