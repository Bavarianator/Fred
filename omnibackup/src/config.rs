//! Konfigurations-Management

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// Hauptkonfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Repository-Konfiguration
    pub repo: RepoConfig,
    
    /// Quellen (zu sichernde Verzeichnisse)
    pub sources: Vec<SourceConfig>,
    
    /// Ziele (Backup-Destinationen)
    pub destinations: Vec<DestinationConfig>,
    
    /// Krypto-Einstellungen
    pub crypto: CryptoConfig,
    
    /// Zeitplan
    pub schedule: ScheduleConfig,
    
    /// Aufbewahrungsregeln
    pub retention: RetentionConfig,
    
    /// Benachrichtigungen
    pub notifications: NotificationConfig,
    
    /// P2P-Einstellungen
    pub p2p: P2PConfig,
    
    /// UI-Einstellungen
    pub ui: UIConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            repo: RepoConfig::default(),
            sources: Vec::new(),
            destinations: Vec::new(),
            crypto: CryptoConfig::default(),
            schedule: ScheduleConfig::default(),
            retention: RetentionConfig::default(),
            notifications: NotificationConfig::default(),
            p2p: P2PConfig::default(),
            ui: UIConfig::default(),
        }
    }
}

impl Config {
    /// Config aus Datei laden oder Wizard starten
    pub fn load_or_wizard() -> Result<Self> {
        let config_path = Self::config_path()?;
        
        if config_path.exists() {
            Self::load(&config_path)
        } else {
            // Wizard starten
            crate::tui::wizard::run_wizard()?;
            Self::load(&config_path)
        }
    }
    
    /// Config laden
    pub fn load(path: &Path) -> Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }
    
    /// Config speichern
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path()?;
        
        // Verzeichnis erstellen falls nicht vorhanden
        if let Some(parent) = config_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        
        let content = toml::to_string_pretty(self)?;
        std::fs::write(config_path, content)?;
        
        Ok(())
    }
    
    /// Standard-Config-Pfad ermitteln
    pub fn config_path() -> Result<PathBuf> {
        let config_dir = dirs::config_dir()
            .ok_or_else(|| anyhow::anyhow!("No config directory found"))?;
        
        Ok(config_dir.join("omnibackup").join("config.toml"))
    }
    
    /// Repository-Pfad ermitteln
    pub fn repo_path(&self) -> PathBuf {
        // Erstes lokales Ziel als Repository-Pfad verwenden
        self.destinations
            .iter()
            .find(|d| d.r#type == "local")
            .map(|d| PathBuf::from(&d.path))
            .unwrap_or_else(|| {
                // Fallback: ~/.local/share/omnibackup
                dirs::data_local_dir()
                    .unwrap_or_else(|| PathBuf::from("/tmp"))
                    .join("omnibackup")
                    .join("repo")
            })
    }
}

/// Repository-Metadaten
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepoConfig {
    /// Eindeutige Repository-ID
    pub id: String,
    
    /// Name des Repositories
    pub name: String,
    
    /// Beschreibung
    pub description: String,
}

impl Default for RepoConfig {
    fn default() -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            name: "My Backup".to_string(),
            description: String::new(),
        }
    }
}

/// Quelle (zu sicherndes Verzeichnis)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceConfig {
    /// Pfad zur Quelle
    pub path: String,
    
    /// Typ: directory, file, database, etc.
    pub r#type: String,
    
    /// Ausschlussmuster (glob patterns)
    pub exclude_patterns: Vec<String>,
    
    /// Versteckte Dateien einschließen
    pub include_hidden: bool,
    
    /// Symlinks folgen
    pub follow_symlinks: bool,
    
    /// Pre-Backup Hook (z.B. DB-Dump)
    pub pre_hook: Option<String>,
    
    /// Post-Backup Hook
    pub post_hook: Option<String>,
}

/// Backup-Ziel
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DestinationConfig {
    /// Anzeigename
    pub name: String,
    
    /// Backend-Typ: local, s3, b2, webdav, nextcloud, p2p, etc.
    pub r#type: String,
    
    /// Lokaler Pfad (für local backend)
    pub path: String,
    
    /// URL (für webdav, nextcloud, etc.)
    pub url: Option<String>,
    
    /// Bucket-Name (für S3, B2, etc.)
    pub bucket: Option<String>,
    
    /// Region (für Cloud-Backends)
    pub region: Option<String>,
    
    /// Access Key / Username
    pub access_key: Option<String>,
    
    /// Secret Key / Password
    pub secret_key: Option<String>,
    
    /// Verschlüsselung aktivieren
    pub encryption: bool,
    
    /// Kompression aktivieren
    pub compression: bool,
    
    /// Maximale parallele Uploads
    pub max_parallel: usize,
    
    /// Bandbreitenbegrenzung (bytes/s)
    pub bandwidth_limit: Option<u64>,
}

/// Krypto-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoConfig {
    /// Passwort-Hash (Argon2id)
    pub password_hash: String,
    
    /// Salt für Key-Derivation
    pub salt: [u8; 16],
    
    /// Verschlüsselungsalgorithmus
    pub algorithm: String,
}

impl Default for CryptoConfig {
    fn default() -> Self {
        Self {
            password_hash: String::new(),
            salt: [0u8; 16],
            algorithm: "age-x25519".to_string(),
        }
    }
}

/// Zeitplan-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleConfig {
    /// Modus: manual, continuous, hourly, daily, weekly
    pub mode: String,
    
    /// Intervall in Minuten (für continuous/hourly)
    pub interval_minutes: Option<u64>,
    
    /// Cron-Ausdruck (für daily/weekly)
    pub cron: Option<String>,
    
    /// Bei USB-Plug automatisch backupen
    pub on_usb_plug: bool,
    
    /// Bei Idle automatisch backupen
    pub on_idle: bool,
    
    /// Nur bei WiFi (Mobile Data vermeiden)
    pub wifi_only: bool,
    
    /// Bandbreite drosseln während Video-Calls
    pub throttle_on_video_call: bool,
}

impl Default for ScheduleConfig {
    fn default() -> Self {
        Self {
            mode: "manual".to_string(),
            interval_minutes: None,
            cron: None,
            on_usb_plug: false,
            on_idle: false,
            wifi_only: false,
            throttle_on_video_call: true,
        }
    }
}

/// Aufbewahrungsregeln (Grandfather-Father-Son)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetentionConfig {
    /// Tägliche Snapshots behalten
    pub keep_daily: usize,
    
    /// Wöchentliche Snapshots behalten
    pub keep_weekly: usize,
    
    /// Monatliche Snapshots behalten
    pub keep_monthly: usize,
    
    /// Jährliche Snapshots behalten
    pub keep_yearly: usize,
    
    /// Mindestens wie viele Snapshots immer behalten
    pub min_snapshots: usize,
}

impl Default for RetentionConfig {
    fn default() -> Self {
        Self {
            keep_daily: 7,
            keep_weekly: 4,
            keep_monthly: 12,
            keep_yearly: 3,
            min_snapshots: 3,
        }
    }
}

/// Benachrichtigungs-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationConfig {
    /// Desktop-Benachrichtigungen
    pub desktop: bool,
    
    /// Webhook-URL
    pub webhook_url: Option<String>,
    
    /// ntfy.sh Topic
    pub ntfy_topic: Option<String>,
    
    /// Telegram Bot Token
    pub telegram_bot_token: Option<String>,
    
    /// Telegram Chat ID
    pub telegram_chat_id: Option<String>,
    
    /// Discord Webhook URL
    pub discord_webhook: Option<String>,
    
    /// Email SMTP Server
    pub smtp_server: Option<String>,
    
    /// Email SMTP Port
    pub smtp_port: Option<u16>,
    
    /// Email Absender
    pub smtp_from: Option<String>,
    
    /// Email Empfänger
    pub smtp_to: Option<String>,
    
    /// Nur bei Fehlern benachrichtigen
    pub only_on_error: bool,
}

impl Default for NotificationConfig {
    fn default() -> Self {
        Self {
            desktop: true,
            webhook_url: None,
            ntfy_topic: None,
            telegram_bot_token: None,
            telegram_chat_id: None,
            discord_webhook: None,
            smtp_server: None,
            smtp_port: None,
            smtp_from: None,
            smtp_to: None,
            only_on_error: false,
        }
    }
}

/// P2P-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct P2PConfig {
    /// P2P aktiviert
    pub enabled: bool,
    
    /// Listen-Port
    pub port: u16,
    
    /// Eigene Peer-ID
    pub peer_id: Option<String>,
    
    /// Bekannte Peers
    pub peers: Vec<PeerConfig>,
    
    /// Erasure Coding: Anzahl benötigter Shards
    pub required_shards: usize,
    
    /// Erasure Coding: Gesamtanzahl Shards
    pub total_shards: usize,
}

impl Default for P2PConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            port: 4001,
            peer_id: None,
            peers: Vec::new(),
            required_shards: 2,
            total_shards: 3,
        }
    }
}

/// Peer-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerConfig {
    /// Peer-ID
    pub peer_id: String,
    
    /// Vertrauenslevel: 0 (none) bis 3 (full)
    pub trust_level: u8,
    
    /// Multiaddr (libp2p)
    pub multiaddr: Option<String>,
    
    /// Angebotener Storage (in Bytes)
    pub offered_storage: u64,
    
    /// Genutzter Storage (in Bytes)
    pub used_storage: u64,
}

/// UI-Konfiguration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIConfig {
    /// Theme: catppuccin, dracula, nord, gruvbox, etc.
    pub theme: String,
    
    /// Sprache: de, en
    pub language: String,
    
    /// Vim-Keybindings aktivieren
    pub vim_mode: bool,
    
    /// Mouse-Support aktivieren
    pub mouse_support: bool,
    
    /// Live-Graphen anzeigen
    pub show_graphs: bool,
    
    /// Kosten anzeigen
    pub show_costs: bool,
}

impl Default for UIConfig {
    fn default() -> Self {
        Self {
            theme: "catppuccin".to_string(),
            language: "de".to_string(),
            vim_mode: false,
            mouse_support: true,
            show_graphs: true,
            show_costs: true,
        }
    }
}

/// Doctor-Check: System-Status prüfen
pub mod doctor {
    use super::*;
    use anyhow::Context;
    
    pub fn run_doctor(config: &Config) -> Result<()> {
        println!("╔══════════════════════════════════════════════════════════════════╗");
        println!("║              🔍  OmniBackup Doctor                               ║");
        println!("╚══════════════════════════════════════════════════════════════════╝");
        println!();
        
        let mut all_ok = true;
        
        // Config-Datei prüfen
        print!("  Config-Datei... ");
        if Config::config_path()?.exists() {
            println!("✅ vorhanden");
        } else {
            println!("❌ fehlt");
            all_ok = false;
        }
        
        // Repository-Pfad prüfen
        print!("  Repository-Pfad... ");
        let repo_path = config.repo_path();
        if repo_path.exists() {
            println!("✅ zugänglich ({:?})", repo_path);
        } else {
            println!("⚠️  existiert nicht (wird beim ersten Backup erstellt)");
        }
        
        // Quellen prüfen
        println!();
        println!("  Quellen:");
        for source in &config.sources {
            print!("    {} ... ", source.path);
            if Path::new(&source.path).exists() {
                println!("✅");
            } else {
                println!("❌ nicht gefunden");
                all_ok = false;
            }
        }
        
        // Ziele prüfen
        println!();
        println!("  Ziele:");
        for dest in &config.destinations {
            print!("    {} ({}) ... ", dest.name, dest.r#type);
            match dest.r#type.as_str() {
                "local" => {
                    if Path::new(&dest.path).exists() {
                        println!("✅");
                    } else {
                        println!("⚠️  wird erstellt");
                    }
                }
                "s3" | "b2" | "r2" => {
                    if dest.bucket.is_some() && dest.access_key.is_some() {
                        println!("✅ konfiguriert");
                    } else {
                        println!("❌ unvollständig");
                        all_ok = false;
                    }
                }
                _ => println!("ℹ️  {}", dest.r#type),
            }
        }
        
        // Krypto prüfen
        println!();
        print!("  Verschlüsselung... ");
        if !config.crypto.password_hash.is_empty() {
            println!("✅ konfiguriert ({})", config.crypto.algorithm);
        } else {
            println!("❌ kein Passwort gesetzt");
            all_ok = false;
        }
        
        // Zeitplan prüfen
        println!();
        print!("  Zeitplan... ");
        println!("ℹ️  {}{}", 
            config.schedule.mode,
            config.schedule.interval_minutes
                .map(|m| format!(" (alle {} min)", m))
                .unwrap_or_default()
        );
        
        println!();
        if all_ok {
            println!("  ✅ Alle Checks bestanden!");
        } else {
            println!("  ⚠️  Einige Probleme gefunden. Bitte obenstehende Fehler beheben.");
        }
        
        Ok(())
    }
}
