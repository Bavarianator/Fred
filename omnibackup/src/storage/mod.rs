// src/storage/mod.rs - Universal Storage Backend Layer
use anyhow::Result;
use bytes::Bytes;
use std::collections::HashMap;

/// Storage backend trait for universal support
#[async_trait::async_trait]
pub trait StorageBackend: Send + Sync {
    fn name(&self) -> &str;
    fn capabilities(&self) -> BackendCapabilities;
    
    async fn put(&self, key: &str, data: Bytes) -> Result<()>;
    async fn get(&self, key: &str) -> Result<Bytes>;
    async fn list(&self, prefix: &str) -> Result<Vec<ObjectMeta>>;
    async fn delete(&self, key: &str) -> Result<()>;
    async fn exists(&self, key: &str) -> Result<bool>;
}

/// Backend capabilities
#[derive(Debug, Clone)]
pub struct BackendCapabilities {
    pub supports_multipart: bool,
    pub supports_range_requests: bool,
    pub supports_versioning: bool,
    pub max_object_size: Option<u64>,
    pub is_immutable: bool,
}

/// Object metadata
#[derive(Debug, Clone)]
pub struct ObjectMeta {
    pub key: String,
    pub size: u64,
    pub last_modified: i64,
    pub etag: Option<String>,
}

/// Local filesystem backend
pub struct LocalBackend {
    root: std::path::PathBuf,
}

impl LocalBackend {
    pub fn new(root: &std::path::Path) -> Self {
        Self {
            root: root.to_path_buf(),
        }
    }
}

#[async_trait::async_trait]
impl StorageBackend for LocalBackend {
    fn name(&self) -> &str {
        "local"
    }

    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            supports_multipart: false,
            supports_range_requests: true,
            supports_versioning: false,
            max_object_size: None,
            is_immutable: false,
        }
    }

    async fn put(&self, key: &str, data: Bytes) -> Result<()> {
        let path = self.root.join(key);
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        tokio::fs::write(path, data.as_ref()).await?;
        Ok(())
    }

    async fn get(&self, key: &str) -> Result<Bytes> {
        let data = tokio::fs::read(self.root.join(key)).await?;
        Ok(Bytes::from(data))
    }

    async fn list(&self, prefix: &str) -> Result<Vec<ObjectMeta>> {
        use tokio_stream::StreamExt;
        let mut entries = Vec::new();
        let mut stream = tokio::fs::read_dir(&self.root)?;
        
        while let Some(entry) = stream.next_entry().await? {
            let path = entry.path();
            let path_str = path.strip_prefix(&self.root)
                .unwrap_or(&path)
                .to_string_lossy()
                .to_string();
            
            if path_str.starts_with(prefix) {
                let meta = entry.metadata().await?;
                entries.push(ObjectMeta {
                    key: path_str,
                    size: meta.len(),
                    last_modified: meta.modified()?
                        .duration_since(std::time::UNIX_EPOCH)?
                        .as_secs() as i64,
                    etag: None,
                });
            }
        }
        
        Ok(entries)
    }

    async fn delete(&self, key: &str) -> Result<()> {
        tokio::fs::remove_file(self.root.join(key)).await?;
        Ok(())
    }

    async fn exists(&self, key: &str) -> Result<bool> {
        Ok(self.root.join(key).exists())
    }
}

/// Storage manager handling multiple backends
pub struct StorageManager {
    backends: HashMap<String, Box<dyn StorageBackend>>,
}

impl StorageManager {
    pub fn new() -> Self {
        Self {
            backends: HashMap::new(),
        }
    }

    pub fn add_backend(&mut self, name: String, backend: Box<dyn StorageBackend>) {
        self.backends.insert(name, backend);
    }

    pub fn get_backend(&self, name: &str) -> Option<&dyn StorageBackend> {
        self.backends.get(name).map(|b| b.as_ref())
    }
}

impl Default for StorageManager {
    fn default() -> Self {
        Self::new()
    }
}
