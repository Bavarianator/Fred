//! Setup-Wizard für Erstkonfiguration

use anyhow::Result;
use std::io::{self, Write};
use crate::config::Config;

/// Interaktiven Wizard starten
pub fn run_wizard() -> Result<()> {
    println!();
    println!("╔══════════════════════════════════════════════════════════════════╗");
    println!("║              🎉  Willkommen bei OmniBackup!                      ║");
    println!("║                                                                  ║");
    println!("║     Das letzte Backup-Tool, das du je brauchen wirst.           ║");
    println!("║                                                                  ║");
    println!("║     Setup dauert ca. 2 Minuten.                                 ║");
    println!("╚══════════════════════════════════════════════════════════════════╝");
    println!();
    
    // Schritt 1: Quellen auswählen
    let sources = step1_sources()?;
    
    // Schritt 2: Ziele auswählen
    let destinations = step2_destinations()?;
    
    // Schritt 3: Verschlüsselung
    let password = step3_encryption()?;
    
    // Schritt 4: Zeitplan
    let schedule = step4_schedule()?;
    
    // Schritt 5: Zusammenfassung
    step5_summary(&sources, &destinations, &schedule)?;
    
    // Config speichern
    let config = Config {
        repo: crate::config::RepoConfig {
            id: uuid::Uuid::new_v4().to_string(),
            name: "My Personal Backup".to_string(),
            description: "Created via wizard".to_string(),
        },
        sources,
        destinations,
        crypto: crate::config::CryptoConfig {
            password_hash: hash_password(&password)?,
            salt: generate_salt(),
        },
        schedule,
        ..Default::default()
    };
    
    config.save()?;
    
    println!();
    println!("✅ Konfiguration gespeichert!");
    println!();
    println!("Erstes Backup jetzt starten? (Y/n)");
    
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    
    if input.trim().to_lowercase().starts_with('n') {
        println!("Kein Problem! Du kannst später 'omnibackup backup' ausführen.");
    } else {
        println!("🚀 Starte erstes Backup...");
        // Backup wird von main() ausgelöst
    }
    
    Ok(())
}

/// Schritt 1: Quellen auswählen
fn step1_sources() -> Result<Vec<crate::config::SourceConfig>> {
    println!();
    println!("Schritt 1/5: Was möchtest du sichern?");
    println!("─────────────────────────────────────────────────────────────────");
    println!();
    
    // Automatisch wichtige Verzeichnisse erkennen
    let suggested = detect_important_directories();
    
    for (i, dir) in suggested.iter().enumerate() {
        let size = estimate_size(&dir.path);
        println!("  [{}] {} {:?} ({}, {} Dateien)", 
            if dir.selected { 'x' } else { ' ' },
            dir.icon,
            dir.path,
            size,
            dir.file_count
        );
    }
    
    println!();
    println!("  [Space] Auswählen  [a] Alle  [n] Keine  [Enter] Weiter");
    println!();
    
    // User-Eingabe verarbeiten (vereinfacht)
    let sources: Vec<crate::config::SourceConfig> = suggested
        .into_iter()
        .filter(|d| d.selected)
        .map(|d| crate::config::SourceConfig {
            path: d.path.to_string_lossy().to_string(),
            r#type: "directory".to_string(),
            exclude_patterns: vec![
                "**/node_modules/**".to_string(),
                "**/.git/**".to_string(),
                "**/__pycache__/**".to_string(),
                "**/*.pyc".to_string(),
                "**/.venv/**".to_string(),
                "**/target/**".to_string(),
                "**/.cache/**".to_string(),
                "**/Downloads/**".to_string(),
                "**/Cache/**".to_string(),
                "**/Temporary/**".to_string(),
            ],
            include_hidden: true,
            follow_symlinks: false,
        })
        .collect();
    
    Ok(sources)
}

/// Wichtige Verzeichnisse automatisch erkennen
fn detect_important_directories() -> Vec<DetectedDir> {
    use std::path::PathBuf;
    
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("/home"));
    
    vec![
        DetectedDir {
            path: home.join("Documents"),
            icon: "📁",
            selected: true,
            file_count: count_files(&home.join("Documents")),
        },
        DetectedDir {
            path: home.join("Pictures"),
            icon: "📷",
            selected: true,
            file_count: count_files(&home.join("Pictures")),
        },
        DetectedDir {
            path: home.join("Videos"),
            icon: "🎬",
            selected: true,
            file_count: count_files(&home.join("Videos")),
        },
        DetectedDir {
            path: home.join("Downloads"),
            icon: "📥",
            selected: false,
            file_count: count_files(&home.join("Downloads")),
        },
        DetectedDir {
            path: home.join("Projects"),
            icon: "💻",
            selected: true,
            file_count: count_files(&home.join("Projects")),
        },
        DetectedDir {
            path: home.join(".config"),
            icon: "⚙️",
            selected: true,
            file_count: count_files(&home.join(".config")),
        },
        DetectedDir {
            path: home.join(".ssh"),
            icon: "🔑",
            selected: true,
            file_count: count_files(&home.join(".ssh")),
        },
    ]
}

/// Hilfstruktur für erkannte Verzeichnisse
struct DetectedDir {
    path: std::path::PathBuf,
    icon: &'static str,
    selected: bool,
    file_count: usize,
}

/// Dateigröße schätzen
fn estimate_size(path: &std::path::Path) -> String {
    use human_size::Size;
    
    if let Ok(size) = fs_extra::dir::get_size(path) {
        Size::from_bytes(size).to_string()
    } else {
        "? GB".to_string()
    }
}

/// Datei-Anzahl zählen
fn count_files(path: &std::path::Path) -> usize {
    if !path.exists() {
        return 0;
    }
    
    walkdir::WalkDir::new(path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .count()
}

/// Schritt 2: Ziele auswählen
fn step2_destinations() -> Result<Vec<crate::config::DestinationConfig>> {
    println!();
    println!("Schritt 2/5: Wohin sichern?");
    println!("─────────────────────────────────────────────────────────────────");
    println!();
    println!("  (1) 💾 Lokal (Externe Festplatte, NAS)");
    println!("  (2) ☁️  Cloud-Anbieter (S3, B2, Azure, GCS, ...)");
    println!("  (3) 🏠 Eigener Server (Nextcloud, MinIO, SFTP, WebDAV)");
    println!("  (4) 🌐 P2P (Familie/Freunde - dezentral)");
    println!("  (5) 🛡️  Hybrid (Empfohlen: Lokal + Cloud = 3-2-1-Regel)");
    println!();
    println!("  💡 Tipp: Die 3-2-1-Regel sagt: 3 Kopien, 2 Medien, 1 Off-Site");
    println!();
    print!("  Auswahl [1-5]: ");
    io::stdout().flush()?;
    
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    
    match input.trim() {
        "1" => Ok(vec![local_destination()?]),
        "2" => Ok(vec![cloud_destination()?]),
        "3" => Ok(vec![server_destination()?]),
        "4" => Ok(vec![p2p_destination()?]),
        "5" | _ => Ok(vec![local_destination()?, cloud_destination()?]),
    }
}

/// Lokales Ziel konfigurieren
fn local_destination() -> Result<crate::config::DestinationConfig> {
    print!("  Backup-Pfad (z.B. /mnt/backup): ");
    io::stdout().flush()?;
    
    let mut path = String::new();
    io::stdin().read_line(&mut path)?;
    
    Ok(crate::config::DestinationConfig {
        name: "Local Backup".to_string(),
        r#type: "local".to_string(),
        path: path.trim().to_string(),
        url: None,
        bucket: None,
        region: None,
        access_key: None,
        secret_key: None,
        encryption: true,
        compression: true,
        max_parallel: 4,
        bandwidth_limit: None,
    })
}

/// Cloud-Ziel konfigurieren
fn cloud_destination() -> Result<crate::config::DestinationConfig> {
    println!();
    println!("  Cloud-Anbieter wählen:");
    println!("    (1) Backblaze B2 (günstigster)");
    println!("    (2) AWS S3");
    println!("    (3) Cloudflare R2 (zero egress)");
    println!("    (4) Wasabi (flat rate)");
    println!();
    print!("  Auswahl [1-4]: ");
    io::stdout().flush()?;
    
    let mut choice = String::new();
    io::stdin().read_line(&mut choice)?;
    
    let provider = match choice.trim() {
        "2" => "s3",
        "3" => "r2",
        "4" => "wasabi",
        _ => "b2",
    };
    
    print!("  Bucket Name: ");
    io::stdout().flush()?;
    let mut bucket = String::new();
    io::stdin().read_line(&mut bucket)?;
    
    print!("  Access Key: ");
    io::stdout().flush()?;
    let mut access_key = String::new();
    io::stdin().read_line(&mut access_key)?;
    
    print!("  Secret Key: ");
    io::stdout().flush()?;
    let mut secret_key = String::new();
    io::stdin().read_line(&mut secret_key)?;
    
    Ok(crate::config::DestinationConfig {
        name: format!("{} Backup", provider.to_uppercase()),
        r#type: provider.to_string(),
        path: String::new(),
        url: None,
        bucket: Some(bucket.trim().to_string()),
        region: Some("eu-central-1".to_string()),
        access_key: Some(access_key.trim().to_string()),
        secret_key: Some(secret_key.trim().to_string()),
        encryption: true,
        compression: true,
        max_parallel: 8,
        bandwidth_limit: None,
    })
}

/// Server-Ziel konfigurieren
fn server_destination() -> Result<crate::config::DestinationConfig> {
    print!("  Server-URL (https://...): ");
    io::stdout().flush()?;
    let mut url = String::new();
    io::stdin().read_line(&mut url)?;
    
    print!("  Username: ");
    io::stdout().flush()?;
    let mut username = String::new();
    io::stdin().read_line(&mut username)?;
    
    print!("  Password: ");
    io::stdout().flush()?;
    let mut password = String::new();
    io::stdin().read_line(&mut password)?;
    
    Ok(crate::config::DestinationConfig {
        name: "Home Server".to_string(),
        r#type: "webdav".to_string(),
        path: "/backups".to_string(),
        url: Some(url.trim().to_string()),
        bucket: None,
        region: None,
        access_key: Some(username.trim().to_string()),
        secret_key: Some(password.trim().to_string()),
        encryption: true,
        compression: true,
        max_parallel: 4,
        bandwidth_limit: None,
    })
}

/// P2P-Ziel konfigurieren
fn p2p_destination() -> Result<crate::config::DestinationConfig> {
    println!("  P2P-Modus erfordert mindestens einen Peer.");
    println!("  Du kannst Peers später mit 'omnibackup p2p peer add <id>' hinzufügen.");
    
    Ok(crate::config::DestinationConfig {
        name: "P2P Network".to_string(),
        r#type: "p2p".to_string(),
        path: String::new(),
        url: None,
        bucket: None,
        region: None,
        access_key: None,
        secret_key: None,
        encryption: true,
        compression: true,
        max_parallel: 4,
        bandwidth_limit: None,
    })
}

/// Schritt 3: Verschlüsselung
fn step3_encryption() -> Result<String> {
    println!();
    println!("Schritt 3/5: Verschlüsselung");
    println!("─────────────────────────────────────────────────────────────────");
    println!();
    println!("  ⚠️  WICHTIG: Ohne Passwort sind Backups VERLOREN!");
    println!();
    print!("  Wähle ein starkes Passwort (mind. 12 Zeichen): ");
    io::stdout().flush()?;
    
    let password = rpassword::prompt_password("")?;
    
    print!("  Bestätigen: ");
    io::stdout().flush()?;
    let confirm = rpassword::prompt_password("")?;
    
    if password != confirm {
        println!("  ❌ Passwörter stimmen nicht überein. Bitte wiederholen.");
        return step3_encryption();
    }
    
    // Passwort-Stärke prüfen
    let strength = check_password_strength(&password);
    println!();
    println!("  Stärke: {}", strength);
    println!();
    
    Ok(password)
}

/// Passwort-Stärke prüfen
fn check_password_strength(password: &str) -> String {
    let mut score = 0;
    
    if password.len() >= 12 { score += 1; }
    if password.len() >= 16 { score += 1; }
    if password.chars().any(|c| c.is_uppercase()) { score += 1; }
    if password.chars().any(|c| c.is_lowercase()) { score += 1; }
    if password.chars().any(|c| c.is_numeric()) { score += 1; }
    if password.chars().any(|c| !c.is_alphanumeric()) { score += 1; }
    
    match score {
        0..=2 => "❌ Zu schwach".to_string(),
        3..=4 => "⚠️  Mittel".to_string(),
        5 => "✅ Stark".to_string(),
        _ => "🔥 Sehr stark".to_string(),
    }
}

/// Salt generieren
fn generate_salt() -> [u8; 16] {
    use rand::RngCore;
    let mut salt = [0u8; 16];
    rand::thread_rng().fill_bytes(&mut salt);
    salt
}

/// Passwort hashen
fn hash_password(password: &str) -> Result<String> {
    use argon2::{Argon2, PasswordHasher, password_hash::SaltString};
    use rand::rngs::OsRng;
    
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let hash = argon2.hash_password(password.as_bytes(), &salt)?;
    
    Ok(hash.to_string())
}

/// Schritt 4: Zeitplan
fn step4_schedule() -> Result<crate::config::ScheduleConfig> {
    println!();
    println!("Schritt 4/5: Zeitplan");
    println!("─────────────────────────────────────────────────────────────────");
    println!();
    println!("  Wann soll gesichert werden?");
    println!();
    println!("  (1) 🔄 Kontinuierlich (bei Datei-Änderung, max. alle 15 min)");
    println!("  (2) ⏰ Stündlich");
    println!("  (3) 📅 Täglich um 02:00 Uhr");
    println!("  (4) 📆 Wöchentlich");
    println!("  (5) 🖱️  Nur manuell");
    println!();
    print!("  Auswahl [1-5]: ");
    io::stdout().flush()?;
    
    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    
    let schedule = match input.trim() {
        "1" => crate::config::ScheduleConfig {
            mode: "continuous".to_string(),
            interval_minutes: Some(15),
            cron: None,
            on_usb_plug: true,
            on_idle: true,
        },
        "2" => crate::config::ScheduleConfig {
            mode: "hourly".to_string(),
            interval_minutes: Some(60),
            cron: Some("0 * * * *".to_string()),
            on_usb_plug: false,
            on_idle: false,
        },
        "4" => crate::config::ScheduleConfig {
            mode: "weekly".to_string(),
            interval_minutes: None,
            cron: Some("0 2 * * 0".to_string()),
            on_usb_plug: false,
            on_idle: false,
        },
        "5" => crate::config::ScheduleConfig {
            mode: "manual".to_string(),
            interval_minutes: None,
            cron: None,
            on_usb_plug: false,
            on_idle: false,
        },
        _ => crate::config::ScheduleConfig {
            mode: "daily".to_string(),
            interval_minutes: None,
            cron: Some("0 2 * * *".to_string()),
            on_usb_plug: false,
            on_idle: false,
        },
    };
    
    println!();
    println!("  Aufbewahrung (Grandfather-Father-Son):");
    print!("  Tägliche Snapshots behalten [7]: ");
    io::stdout().flush()?;
    let mut keep_daily = String::new();
    io::stdin().read_line(&mut keep_daily)?;
    
    print!("  Wöchentliche Snapshots behalten [4]: ");
    io::stdout().flush()?;
    let mut keep_weekly = String::new();
    io::stdin().read_line(&mut keep_weekly)?;
    
    print!("  Monatliche Snapshots behalten [12]: ");
    io::stdout().flush()?;
    let mut keep_monthly = String::new();
    io::stdin().read_line(&mut keep_monthly)?;
    
    Ok(schedule)
}

/// Schritt 5: Zusammenfassung
fn step5_summary(
    sources: &[crate::config::SourceConfig],
    destinations: &[crate::config::DestinationConfig],
    schedule: &crate::config::ScheduleConfig,
) -> Result<()> {
    println!();
    println!("Schritt 5/5: Zusammenfassung");
    println!("─────────────────────────────────────────────────────────────────");
    println!();
    
    let total_paths: usize = sources.len();
    let dest_names: Vec<&str> = destinations.iter().map(|d| d.name.as_str()).collect();
    
    println!("  📋 Quellen:        {} Verzeichnisse", total_paths);
    println!("  🎯 Ziel:           {}", dest_names.join(" + "));
    println!("  🔒 Verschlüsselung: AES-256 + age (X25519)");
    println!("  ⏰ Zeitplan:        {}", schedule.mode);
    println!();
    
    println!("  [ ✓ Fertig! ]");
    println!();
    
    Ok(())
}
