// src/storage/s3.rs - Native AWS S3 Backend
use anyhow::Result;
use bytes::Bytes;
use aws_sdk_s3::{Client, Config, Region};
use aws_credential_types::Credentials;
use crate::storage::{StorageBackend, BackendCapabilities, ObjectMeta};
use std::collections::HashMap;

/// S3 Storage Backend
pub struct S3Backend {
    client: Client,
    bucket: String,
    prefix: Option<String>,
}

impl S3Backend {
    /// Create new S3 backend
    pub async fn new(
        access_key: &str,
        secret_key: &str,
        region: &str,
        bucket: &str,
        endpoint: Option<&str>,
    ) -> Result<Self> {
        let credentials = Credentials::from_keys(access_key.to_string(), secret_key.to_string(), None);
        
        let config_builder = Config::builder()
            .credentials_provider(credentials)
            .region(Region::new(region.to_string()));
        
        let config = if let Some(ep) = endpoint {
            config_builder.endpoint_url(ep).build()
        } else {
            config_builder.build()
        };
        
        let client = Client::from_conf(config);
        
        Ok(Self {
            client,
            bucket: bucket.to_string(),
            prefix: None,
        })
    }
    
    /// Set prefix for all keys
    pub fn with_prefix(mut self, prefix: &str) -> Self {
        self.prefix = Some(prefix.to_string());
        self
    }
    
    fn make_key(&self, key: &str) -> String {
        match &self.prefix {
            Some(prefix) => format!("{}/{}", prefix, key),
            None => key.to_string(),
        }
    }
}

#[async_trait::async_trait]
impl StorageBackend for S3Backend {
    fn name(&self) -> &str {
        "s3"
    }

    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            supports_multipart: true,
            supports_range_requests: true,
            supports_versioning: true,
            max_object_size: Some(5 * 1024 * 1024 * 1024 * 1024), // 5TB
            is_immutable: false,
        }
    }

    async fn put(&self, key: &str, data: Bytes) -> Result<()> {
        let s3_key = self.make_key(key);
        
        self.client
            .put_object()
            .bucket(&self.bucket)
            .key(&s3_key)
            .body(data.into())
            .send()
            .await?;
        
        Ok(())
    }

    async fn get(&self, key: &str) -> Result<Bytes> {
        let s3_key = self.make_key(key);
        
        let response = self.client
            .get_object()
            .bucket(&self.bucket)
            .key(&s3_key)
            .send()
            .await?;
        
        let body = response.body.collect().await?;
        Ok(body.into_bytes())
    }

    async fn list(&self, prefix: &str) -> Result<Vec<ObjectMeta>> {
        let s3_prefix = self.make_key(prefix);
        
        let mut objects = Vec::new();
        let mut continuation_token = None;
        
        loop {
            let mut request = self.client
                .list_objects_v2()
                .bucket(&self.bucket)
                .prefix(&s3_prefix);
            
            if let Some(token) = continuation_token.take() {
                request = request.continuation_token(token);
            }
            
            let response = request.send().await?;
            
            for obj in response.contents.unwrap_or_default() {
                objects.push(ObjectMeta {
                    key: obj.key.unwrap_or_default(),
                    size: obj.size as u64,
                    last_modified: obj.last_modified
                        .map(|t| t.as_secs_f64() as i64)
                        .unwrap_or(0),
                    etag: obj.etag.map(|e| e.trim_matches('"').to_string()),
                });
            }
            
            if !response.is_truncated.unwrap_or(false) {
                break;
            }
            
            continuation_token = response.next_continuation_token;
        }
        
        Ok(objects)
    }

    async fn delete(&self, key: &str) -> Result<()> {
        let s3_key = self.make_key(key);
        
        self.client
            .delete_object()
            .bucket(&self.bucket)
            .key(&s3_key)
            .send()
            .await?;
        
        Ok(())
    }

    async fn exists(&self, key: &str) -> Result<bool> {
        let s3_key = self.make_key(key);
        
        match self.client.head_object().bucket(&self.bucket).key(&s3_key).send().await {
            Ok(_) => Ok(true),
            Err(aws_sdk_s3::types::SdkError::ServiceError(e)) => {
                if e.err().code() == Some("NotFound") || e.err().code() == Some("404") {
                    Ok(false)
                } else {
                    Err(e.into())
                }
            }
            Err(e) => Err(e.into()),
        }
    }
}

pub fn placeholder() -> &'static str {
    "S3 backend loaded"
}
