// src/core/migrate.rs - Migration from other Backup Tools
use anyhow::Result;
use std::path::{Path, PathBuf};

pub struct Migrator {
    source_type: BackupType,
    source_path: PathBuf,
}

#[derive(Debug, Clone)]
pub enum BackupType {
    Restic,
    Borg,
    Duplicati,
    Kopia,
    Rsync,
}

impl Migrator {
    pub fn new(backup_type: &str, path: &Path) -> Result<Self> {
        let source_type = match backup_type.to_lowercase().as_str() {
            "restic" => BackupType::Restic,
            "borg" => BackupType::Borg,
            "duplicati" => BackupType::Duplicati,
            "kopia" => BackupType::Kopia,
            "rsync" => BackupType::Rsync,
            _ => anyhow::bail!("Unsupported backup type: {}", backup_type),
        };

        Ok(Self {
            source_type,
            source_path: path.to_path_buf(),
        })
    }

    pub fn analyze(&self) -> Result<MigrationReport> {
        let mut report = MigrationReport {
            source_type: format!("{:?}", self.source_type),
            source_path: self.source_path.clone(),
            ..Default::default()
        };

        // Check if source exists
        if !self.source_path.exists() {
            report.errors.push("Source path does not exist".to_string());
            return Ok(report);
        }

        // Analyze based on type
        match self.source_type {
            BackupType::Restic => self.analyze_restic(&mut report)?,
            BackupType::Borg => self.analyze_borg(&mut report)?,
            BackupType::Duplicati => self.analyze_duplicati(&mut report)?,
            BackupType::Kopia => self.analyze_kopia(&mut report)?,
            BackupType::Rsync => self.analyze_rsync(&mut report)?,
        }

        Ok(report)
    }

    fn analyze_restic(&self, report: &mut MigrationReport) -> Result<()> {
        // Restic stores data in data/* directories
        let data_dir = self.source_path.join("data");
        if data_dir.exists() {
            report.found_snapshots = true;
            // Count pack files
            if let Ok(entries) = std::fs::read_dir(&data_dir) {
                for entry in entries.flatten() {
                    if entry.path().is_dir() {
                        if let Ok(packs) = std::fs::read_dir(entry.path()) {
                            report.total_size += packs.count() as u64 * 1024 * 1024; // Estimate
                        }
                    }
                }
            }
        }
        Ok(())
    }

    fn analyze_borg(&self, report: &mut MigrationReport) -> Result<()> {
        // Borg uses a different structure
        if self.source_path.join("config").exists() {
            report.found_snapshots = true;
        }
        Ok(())
    }

    fn analyze_duplicati(&self, report: &mut MigrationReport) -> Result<()> {
        if self.source_path.extension().map_or(false, |e| e == "sqlite") {
            report.found_snapshots = true;
        }
        Ok(())
    }

    fn analyze_kopia(&self, report: &mut MigrationReport) -> Result<()> {
        if self.source_path.join("kopia.repository").exists() {
            report.found_snapshots = true;
        }
        Ok(())
    }

    fn analyze_rsync(&self, report: &mut MigrationReport) -> Result<()> {
        // Simple directory scan
        report.total_size = Self::dir_size(&self.source_path)?;
        report.found_snapshots = true;
        Ok(())
    }

    fn dir_size(path: &Path) -> Result<u64> {
        let mut size = 0;
        if path.is_dir() {
            for entry in std::fs::read_dir(path)? {
                if let Ok(entry) = entry {
                    if entry.path().is_dir() {
                        size += Self::dir_size(&entry.path())?;
                    } else {
                        size += entry.metadata()?.len();
                    }
                }
            }
        }
        Ok(size)
    }

    pub fn execute(&self, target: &Path, dry_run: bool) -> Result<MigrationReport> {
        let mut report = self.analyze()?;
        report.target_path = Some(target.to_path_buf());
        report.dry_run = dry_run;
        
        if !dry_run {
            // TODO: Implement actual migration logic
            report.status = "Migration not yet implemented".to_string();
        } else {
            report.status = "Dry run - no changes made".to_string();
        }
        
        Ok(report)
    }
}

#[derive(Debug, Default)]
pub struct MigrationReport {
    pub source_type: String,
    pub source_path: PathBuf,
    pub target_path: Option<PathBuf>,
    pub found_snapshots: bool,
    pub total_size: u64,
    pub snapshot_count: usize,
    pub dry_run: bool,
    pub status: String,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}
