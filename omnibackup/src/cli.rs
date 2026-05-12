//! CLI-Definition mit Clap

use clap::{Parser, Subcommand};
use crate::config::Config;
use anyhow::Result;

#[derive(Parser)]
#[command(name = "omnibackup")]
#[command(author = "OmniBackup Team")]
#[command(version = "1.0.0")]
#[command(about = "Das ultimative Backup-Tool", long_about = None)]
pub struct Cli {
    /// Verbose output
    #[arg(short, long)]
    pub verbose: bool,
    
    /// Config file path
    #[arg(short, long)]
    pub config: Option<String>,
    
    #[command(subcommand)]
    pub command: Option<Commands>,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Startet den Setup-Wizard
    Init,
    
    /// Backup aller Quellen ausführen
    Backup {
        /// Spezifische Quelle
        #[arg(short, long)]
        source: Option<String>,
        
        /// Ziel-Backend(s)
        #[arg(short, long)]
        dest: Vec<String>,
        
        /// Tag für Snapshot
        #[arg(long)]
        tag: Option<String>,
    },
    
    /// Wiederherstellen interaktiv
    Restore {
        /// Snapshot ID oder 'latest'
        #[arg(long)]
        snapshot: Option<String>,
        
        /// Ziel-Pfad für Restore
        #[arg(long)]
        target: Option<String>,
        
        /// Spezifische Datei wiederherstellen
        #[arg(long)]
        file: Option<String>,
        
        /// Zeitpunkt für Time-Machine-Restore
        #[arg(long)]
        time: Option<String>,
    },
    
    /// Snapshots verwalten
    Snapshots {
        #[command(subcommand)]
        action: SnapshotCommands,
    },
    
    /// Repository verifizieren
    Verify {
        /// Snapshot ID
        #[arg(long)]
        snapshot: Option<String>,
        
        /// Deep verification (alle Chunks)
        #[arg(long)]
        deep: bool,
    },
    
    /// Reparatur versuchen
    Repair {
        /// Snapshot ID
        #[arg(long)]
        snapshot: String,
    },
    
    /// Snapshot als FUSE mounten
    Mount {
        /// Snapshot ID
        snapshot_id: String,
        
        /// Mount-Punkt
        mount_point: String,
    },
    
    /// FUSE unmounten
    Unmount {
        /// Mount-Punkt
        mount_point: String,
    },
    
    /// Quellen verwalten
    Sources {
        #[command(subcommand)]
        action: SourceCommands,
    },
    
    /// Ziele verwalten
    Dest {
        #[command(subcommand)]
        action: DestCommands,
    },
    
    /// P2P-Modus
    P2P {
        #[command(subcommand)]
        action: P2PCommands,
    },
    
    /// Konfiguration bearbeiten/anzeigen
    Config {
        #[command(subcommand)]
        action: ConfigCommands,
    },
    
    /// Statistiken anzeigen
    Stats,
    
    /// Logs anzeigen
    Logs {
        /// Anzahl Zeilen
        #[arg(long, default_value = "100")]
        tail: usize,
    },
    
    /// Prometheus Metrics
    Metrics,
    
    /// Garbage Collection
    Gc,
    
    /// Repository optimieren
    Optimize,
    
    /// Von anderem Tool migrieren
    Migrate {
        /// Quell-Tool (restic, borg, rclone)
        from: String,
        
        /// Quell-Pfad
        path: String,
    },
    
    /// Recovery-Key anzeigen
    RecoveryKey {
        #[command(subcommand)]
        action: RecoveryKeyCommands,
    },
    
    /// System-Check
    Doctor,
}

#[derive(Subcommand)]
pub enum SnapshotCommands {
    /// Alle Snapshots auflisten
    List,
    /// Snapshot-Details anzeigen
    Show { id: String },
    /// Unterschied zwischen Snapshots
    Diff { id1: String, id2: String },
    /// Alte Snapshots löschen
    Prune {
        #[arg(long)]
        keep_daily: Option<usize>,
        #[arg(long)]
        keep_weekly: Option<usize>,
        #[arg(long)]
        keep_monthly: Option<usize>,
        #[arg(long)]
        keep_yearly: Option<usize>,
    },
    /// Snapshot taggen
    Tag { id: String, tag: String },
}

#[derive(Subcommand)]
pub enum SourceCommands {
    /// Quelle hinzufügen
    Add { path: String },
    /// Quelle entfernen
    Remove { path: String },
    /// Alle Quellen auflisten
    List,
    /// Smart-Detection erneut ausführen
    Scan,
}

#[derive(Subcommand)]
pub enum DestCommands {
    /// Ziel hinzufügen
    Add {
        /// Backend-Typ (s3, b2, nextcloud, webdav, local, ...)
        #[arg(long)]
        r#type: String,
        
        /// Bucket/Path/URL
        #[arg(long)]
        bucket: Option<String>,
        
        /// URL für WebDAV/Nextcloud
        #[arg(long)]
        url: Option<String>,
    },
    /// Verbindung testen
    Test { name: String },
    /// Alle Ziele auflisten
    List,
}

#[derive(Subcommand)]
pub enum P2PCommands {
    /// P2P-Node starten
    Start {
        #[arg(long, default_value = "4001")]
        port: u16,
    },
    /// Peer hinzufügen
    PeerAdd { peer_id: String },
    /// Peer vertrauen
    PeerTrust { peer_id: String },
    /// P2P-Status anzeigen
    Status,
}

#[derive(Subcommand)]
pub enum ConfigCommands {
    /// Config im Editor öffnen
    Edit,
    /// Config anzeigen
    Show,
    /// Config exportieren
    Export,
    /// Config importieren
    Import { file: String },
}

#[derive(Subcommand)]
pub enum RecoveryKeyCommands {
    /// Recovery-Key anzeigen
    Show,
    /// Recovery-Key rotieren
    Rotate,
}

impl Commands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            Commands::Init => crate::tui::wizard::run_wizard()?,
            Commands::Backup { source, dest, tag } => {
                crate::core::backup::run_backup(&config, source.as_deref(), &dest, tag.as_deref()).await?
            }
            Commands::Restore { snapshot, target, file, time } => {
                crate::recovery::restore::run_restore(&config, snapshot.as_deref(), target.as_deref(), file.as_deref(), time.as_deref()).await?
            }
            Commands::Snapshots { action } => action.execute(config).await?,
            Commands::Verify { snapshot, deep } => {
                crate::recovery::verify::verify_snapshot(&config, snapshot.as_deref(), deep).await?
            }
            Commands::Repair { snapshot } => {
                crate::recovery::repair::repair_snapshot(&config, &snapshot).await?
            }
            Commands::Mount { snapshot_id, mount_point } => {
                crate::recovery::mount::mount_snapshot(&config, &snapshot_id, &mount_point).await?
            }
            Commands::Unmount { mount_point } => {
                crate::recovery::mount::unmount_snapshot(&mount_point)?
            }
            Commands::Sources { action } => action.execute(config).await?,
            Commands::Dest { action } => action.execute(config).await?,
            Commands::P2P { action } => action.execute(config).await?,
            Commands::Config { action } => action.execute(config).await?,
            Commands::Stats => crate::core::stats::show_stats(&config)?,
            Commands::Logs { tail } => crate::db::logs::show_logs(tail)?,
            Commands::Metrics => crate::notifications::metrics::export_metrics(&config)?,
            Commands::Gc => crate::core::gc::run_gc(&config)?,
            Commands::Optimize => crate::core::optimize::run_optimize(&config)?,
            Commands::Migrate { from, path } => {
                crate::core::migrate::migrate_from(&config, &from, &path).await?
            }
            Commands::RecoveryKey { action } => action.execute(config).await?,
            Commands::Doctor => crate::config::doctor::run_doctor(&config)?,
        }
        
        Ok(())
    }
}

impl SnapshotCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            SnapshotCommands::List => crate::core::snapshot::list_snapshots(&config)?,
            SnapshotCommands::Show { id } => crate::core::snapshot::show_snapshot(&config, &id)?,
            SnapshotCommands::Diff { id1, id2 } => crate::core::snapshot::diff_snapshots(&config, &id1, &id2)?,
            SnapshotCommands::Prune { keep_daily, keep_weekly, keep_monthly, keep_yearly } => {
                crate::core::snapshot::prune_snapshots(&config, keep_daily, keep_weekly, keep_monthly, keep_yearly).await?
            }
            SnapshotCommands::Tag { id, tag } => crate::core::snapshot::tag_snapshot(&config, &id, &tag)?,
        }
        Ok(())
    }
}

impl SourceCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            SourceCommands::Add { path } => crate::config::sources::add_source(&config, &path)?,
            SourceCommands::Remove { path } => crate::config::sources::remove_source(&config, &path)?,
            SourceCommands::List => crate::config::sources::list_sources(&config)?,
            SourceCommands::Scan => crate::config::sources::scan_sources(&config)?,
        }
        Ok(())
    }
}

impl DestCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            DestCommands::Add { r#type, bucket, url } => {
                crate::config::destinations::add_destination(&config, &r#type, bucket.as_deref(), url.as_deref())?
            }
            DestCommands::Test { name } => crate::config::destinations::test_destination(&config, &name).await?,
            DestCommands::List => crate::config::destinations::list_destinations(&config)?,
        }
        Ok(())
    }
}

impl P2PCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            P2PCommands::Start { port } => crate::p2p::node::start_node(&config, port).await?,
            P2PCommands::PeerAdd { peer_id } => crate::p2p::peers::add_peer(&config, &peer_id)?,
            P2PCommands::PeerTrust { peer_id } => crate::p2p::peers::trust_peer(&config, &peer_id)?,
            P2PCommands::Status => crate::p2p::status::show_status(&config)?,
        }
        Ok(())
    }
}

impl ConfigCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            ConfigCommands::Edit => crate::config::edit::edit_config()?,
            ConfigCommands::Show => crate::config::show::show_config(&config)?,
            ConfigCommands::Export => crate::config::export::export_config(&config)?,
            ConfigCommands::Import { file } => crate::config::import::import_config(&file)?,
        }
        Ok(())
    }
}

impl RecoveryKeyCommands {
    pub async fn execute(self, config: Config) -> Result<()> {
        match self {
            RecoveryKeyCommands::Show => crate::core::crypto::show_recovery_key(&config)?,
            RecoveryKeyCommands::Rotate => crate::core::crypto::rotate_recovery_key(&config)?,
        }
        Ok(())
    }
}
