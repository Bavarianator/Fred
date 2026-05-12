// src/core/index.rs - SQLite-based Index Management
use anyhow::Result;
use sqlx::{SqlitePool, SqliteConnection};
use std::path::Path;

/// Index manager for backup metadata
pub struct IndexManager {
    pool: SqlitePool,
}

impl IndexManager {
    pub async fn new(db_path: &Path) -> Result<Self> {
        let pool = SqlitePool::connect(db_path.to_str().unwrap()).await?;
        
        // Run migrations
        Self::migrate(&pool).await?;
        
        Ok(Self { pool })
    }

    async fn migrate(pool: &SqlitePool) -> Result<()> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                source_path TEXT NOT NULL,
                file_count INTEGER DEFAULT 0,
                total_size INTEGER DEFAULT 0,
                compressed_size INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                tags TEXT DEFAULT ''
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                path TEXT NOT NULL,
                size INTEGER NOT NULL,
                mtime INTEGER NOT NULL,
                mode INTEGER,
                uid INTEGER,
                gid INTEGER,
                chunk_ids TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
            )
            "#,
        )
        .execute(pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                ref_count INTEGER DEFAULT 1,
                storage_path TEXT NOT NULL
            )
            "#,
        )
        .execute(pool)
        .await?;

        // Create indexes for performance
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_files_snapshot ON files(snapshot_id)")
            .execute(pool)
            .await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
            .execute(pool)
            .await?;

        Ok(())
    }

    pub async fn add_snapshot(&self, snapshot: &SnapshotInfo) -> Result<()> {
        sqlx::query(
            r#"
            INSERT INTO snapshots (id, created_at, source_path, file_count, total_size, compressed_size, status, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&snapshot.id)
        .bind(snapshot.created_at)
        .bind(&snapshot.source_path)
        .bind(snapshot.file_count)
        .bind(snapshot.total_size)
        .bind(snapshot.compressed_size)
        .bind(&snapshot.status)
        .bind(&snapshot.tags.join(","))
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    pub async fn add_file(&self, snapshot_id: &str, file: &FileInfo) -> Result<()> {
        sqlx::query(
            r#"
            INSERT INTO files (snapshot_id, path, size, mtime, mode, uid, gid, chunk_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(snapshot_id)
        .bind(&file.path)
        .bind(file.size)
        .bind(file.mtime)
        .bind(file.mode)
        .bind(file.uid)
        .bind(file.gid)
        .bind(&file.chunk_ids.join(","))
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    pub async fn get_snapshot(&self, id: &str) -> Result<Option<SnapshotInfo>> {
        let row = sqlx::query_as::<_, SnapshotRow>(
            "SELECT * FROM snapshots WHERE id = ?",
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(row.map(|r| r.into()))
    }

    pub async fn list_snapshots(&self) -> Result<Vec<SnapshotInfo>> {
        let rows = sqlx::query_as::<_, SnapshotRow>(
            "SELECT * FROM snapshots ORDER BY created_at DESC",
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(rows.into_iter().map(|r| r.into()).collect())
    }

    pub async fn update_snapshot_status(&self, id: &str, status: &str) -> Result<()> {
        sqlx::query("UPDATE snapshots SET status = ? WHERE id = ?")
            .bind(status)
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(())
    }

    pub async fn delete_snapshot(&self, id: &str) -> Result<()> {
        // Delete associated files first
        sqlx::query("DELETE FROM files WHERE snapshot_id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;

        // Then delete snapshot
        sqlx::query("DELETE FROM snapshots WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct SnapshotInfo {
    pub id: String,
    pub created_at: i64,
    pub source_path: String,
    pub file_count: i32,
    pub total_size: i64,
    pub compressed_size: i64,
    pub status: String,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct FileInfo {
    pub path: String,
    pub size: i64,
    pub mtime: i64,
    pub mode: Option<i32>,
    pub uid: Option<i32>,
    pub gid: Option<i32>,
    pub chunk_ids: Vec<String>,
}

struct SnapshotRow {
    id: String,
    created_at: i64,
    source_path: String,
    file_count: i32,
    total_size: i64,
    compressed_size: i64,
    status: String,
    tags: String,
}

impl From<SnapshotRow> for SnapshotInfo {
    fn from(row: SnapshotRow) -> Self {
        Self {
            id: row.id,
            created_at: row.created_at,
            source_path: row.source_path,
            file_count: row.file_count,
            total_size: row.total_size,
            compressed_size: row.compressed_size,
            status: row.status,
            tags: row.tags.split(',').map(String::from).filter(|s| !s.is_empty()).collect(),
        }
    }
}
