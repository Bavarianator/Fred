//! OmniBackup – Das ultimative Backup-Tool
//! 
//! Ein autonomes, verschlüsseltes, dedupliziertes Backup-System mit TUI.

mod cli;
mod tui;
mod core;
mod storage;
mod p2p;
mod scheduler;
mod hooks;
mod notifications;
mod recovery;
mod config;
mod db;
mod error;

use anyhow::Result;
use clap::Parser;
use cli::Cli;
use config::Config;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // CLI parsing
    let cli = Cli::parse();
    
    // Logging initialisieren
    init_logging(&cli)?;
    
    // Config laden oder Wizard starten
    let config = Config::load_or_wizard()?;
    
    // Hauptbefehl ausführen
    match cli.command {
        Some(cmd) => cmd.execute(config).await?,
        None => {
            // Keine CLI-Befehle → TUI starten
            tui::run_tui(config).await?;
        }
    }
    
    Ok(())
}

/// Logging-Subsystem initialisieren
fn init_logging(cli: &Cli) -> Result<()> {
    let log_level = cli.verbose.then_some("debug").unwrap_or("info");
    
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(log_level))
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .init();
    
    tracing::info!("OmniBackup v{} gestartet", env!("CARGO_PKG_VERSION"));
    
    Ok(())
}
