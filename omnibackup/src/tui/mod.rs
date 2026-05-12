//! TUI-Implementation mit Ratatui

mod app;
mod events;
mod wizard;
mod theme;
mod views;

pub use app::App;
pub use wizard::run_wizard;

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{io, time::Duration};
use crate::config::Config;

/// Haupt-TUI-Loop starten
pub async fn run_tui(config: Config) -> Result<()> {
    // Terminal setup
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // App-State initialisieren
    let mut app = App::new(config);
    
    // Main loop
    let res = run_app(&mut terminal, &mut app).await;
    
    // Terminal restore
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;
    
    if let Err(err) = res {
        eprintln!("TUI Error: {:?}", err);
    }
    
    Ok(())
}

/// App-Event-Loop
async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
) -> Result<()> {
    use tokio::time::sleep;
    
    loop {
        // Render
        terminal.draw(|f| app.render(f))?;
        
        // Events verarbeiten (mit Timeout für Async-Updates)
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if let Some(action) = app.handle_key(key) {
                    match action {
                        AppAction::Quit => return Ok(()),
                        AppAction::Backup => app.start_backup().await?,
                        AppAction::Restore => app.open_restore()?,
                        AppAction::Settings => app.open_settings()?,
                        AppAction::Help => app.toggle_help()?,
                        _ => {}
                    }
                }
            }
        }
        
        // Background tasks updaten
        app.update().await?;
    }
}

/// App-Aktionen
#[derive(Debug, Clone)]
pub enum AppAction {
    None,
    Quit,
    Backup,
    Restore,
    Settings,
    Help,
    NavigateUp,
    NavigateDown,
    NavigateLeft,
    NavigateRight,
    Select,
    Cancel,
}

impl Default for AppAction {
    fn default() -> Self {
        AppAction::None
    }
}
