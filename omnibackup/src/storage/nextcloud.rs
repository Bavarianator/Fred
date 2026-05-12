// src/storage/nextcloud.rs - Native Nextcloud API Backend
use anyhow::Result;
use bytes::Bytes;
use reqwest::{Client, StatusCode};
use crate::storage::{StorageBackend, BackendCapabilities, ObjectMeta};

/// Nextcloud Storage Backend
pub struct NextcloudBackend {
    client: Client,
    base_url: String,
    username: String,
    password: String,
}

impl NextcloudBackend {
    /// Create new Nextcloud backend
    pub fn new(base_url: &str, username: &str, password: &str) -> Result<Self> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(300))
            .build()?;
        
        Ok(Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
            username: username.to_string(),
            password: password.to_string(),
        })
    }
    
    fn webdav_url(&self, path: &str) -> String {
        format!("{}/remote.php/dav/files/{}/{}", self.base_url, self.username, path.trim_start_matches('/'))
    }
}

#[async_trait::async_trait]
impl StorageBackend for NextcloudBackend {
    fn name(&self) -> &str {
        "nextcloud"
    }

    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            supports_multipart: true,
            supports_range_requests: true,
            supports_versioning: false,
            max_object_size: Some(10 * 1024 * 1024 * 1024), // 10GB (Nextcloud limit)
            is_immutable: false,
        }
    }

    async fn put(&self, key: &str, data: Bytes) -> Result<()> {
        let url = self.webdav_url(key);
        
        let response = self.client
            .put(&url)
            .basic_auth(&self.username, Some(&self.password))
            .body(data)
            .send()
            .await?;
        
        if response.status().is_success() || response.status() == StatusCode::CREATED {
            Ok(())
        } else {
            anyhow::bail!("Upload failed: {}", response.status())
        }
    }

    async fn get(&self, key: &str) -> Result<Bytes> {
        let url = self.webdav_url(key);
        
        let response = self.client
            .get(&url)
            .basic_auth(&self.username, Some(&self.password))
            .send()
            .await?;
        
        if !response.status().is_success() {
            anyhow::bail!("Download failed: {}", response.status())
        }
        
        let data = response.bytes().await?;
        Ok(data)
    }

    async fn list(&self, prefix: &str) -> Result<Vec<ObjectMeta>> {
        use xml::reader::{Reader, XmlEvent};
        
        let url = format!("{}/remote.php/dav/files/{}/{}", 
            self.base_url, self.username, prefix.trim_start_matches('/'));
        
        // PROPFIND request to list files
        let propfind_body = r#"<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:">
    <d:prop>
        <d:getcontentlength/>
        <d:getlastmodified/>
        <d:getetag/>
        <d:resourcetype/>
    </d:prop>
</d:propfind>"#;
        
        let response = self.client
            .request(reqwest::Method::from_bytes(b"PROPFIND")?, &url)
            .basic_auth(&self.username, Some(&self.password))
            .header("Depth", "infinity")
            .body(propfind_body)
            .send()
            .await?;
        
        if !response.status().is_success() {
            anyhow::bail!("List failed: {}", response.status())
        }
        
        let xml_text = response.text().await?;
        let mut objects = Vec::new();
        
        // Simple XML parsing (could be improved with proper XML library)
        let reader = Reader::from_str(&xml_text);
        for event in reader.into_iter().flatten() {
            if let XmlEvent::StartElement { ref name, .. } = event {
                if name.local_name == "response" {
                    // Parse response element
                    // This is simplified - full implementation would parse all fields
                }
            }
        }
        
        Ok(objects)
    }

    async fn delete(&self, key: &str) -> Result<()> {
        let url = self.webdav_url(key);
        
        let response = self.client
            .delete(&url)
            .basic_auth(&self.username, Some(&self.password))
            .send()
            .await?;
        
        if response.status().is_success() || response.status() == StatusCode::NO_CONTENT {
            Ok(())
        } else {
            anyhow::bail!("Delete failed: {}", response.status())
        }
    }

    async fn exists(&self, key: &str) -> Result<bool> {
        let url = self.webdav_url(key);
        
        let response = self.client
            .request(reqwest::Method::from_bytes(b"PROPFIND")?, &url)
            .basic_auth(&self.username, Some(&self.password))
            .header("Depth", "0")
            .send()
            .await?;
        
        Ok(response.status().is_success())
    }
}

pub fn placeholder() -> &'static str {
    "Nextcloud backend loaded"
}
