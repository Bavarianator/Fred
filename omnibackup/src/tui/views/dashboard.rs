// src/tui/views/dashboard.rs - Haupt-Dashboard View
use ratatui::{
    Frame,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Gauge, Paragraph, Wrap},
};

use crate::core::stats::{BackupStats, LiveProgress, BackupPhase};

pub fn render_dashboard(frame: &mut Frame, area: Rect, stats: &BackupStats, progress: Option<&LiveProgress>) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(10),    // Main content
            Constraint::Length(3),  // Footer
        ])
        .split(area);

    // Header
    let header = Paragraph::new(Line::from(vec![
        Span::styled("🛡️  OmniBackup", Style::default().fg(Color::Cyan).add_modifier(ratatui::style::Modifier::BOLD)),
        Span::raw(" | "),
        Span::styled(format!("v{}", env!("CARGO_PKG_VERSION")), Style::default().fg(Color::DarkGray)),
    ]))
    .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::Blue)));
    frame.render_widget(header, chunks[0]);

    // Main content split
    let main_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(40),  // Sources
            Constraint::Percentage(60),  // Status/Progress
        ])
        .split(chunks[1]);

    // Left panel - Sources summary
    let sources_text = vec![
        Line::from(Span::raw("📁 Quellen:")),
        Line::from(format!("   Dokumente: {} GB", (stats.total_size as f64 / 1024.0 / 1024.0 / 1024.0 * 0.3).round())),
        Line::from(format!("   Bilder: {} GB", (stats.total_size as f64 / 1024.0 / 1024.0 / 1024.0 * 0.5).round())),
        Line::from(format!("   Projekte: {} GB", (stats.total_size as f64 / 1024.0 / 1024.0 / 1024.0 * 0.2).round())),
        Line::from(""),
        Line::from(Span::raw("💾 Ziele:")),
        Line::from("   ☁️  Backblaze B2"),
        Line::from("   🏠 Nextcloud"),
        Line::from("   💾 Externe HDD"),
    ];
    
    let sources = Paragraph::new(sources_text)
        .block(Block::default()
            .title(" Quellen ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Green)))
        .wrap(Wrap { trim: false });
    frame.render_widget(sources, main_chunks[0]);

    // Right panel - Status or Progress
    if let Some(prog) = progress {
        render_progress_panel(frame, main_chunks[1], prog);
    } else {
        render_status_panel(frame, main_chunks[1], stats);
    }

    // Footer with keybindings
    let footer = Paragraph::new(Line::from(vec![
        Span::styled("[F2]", Style::default().fg(Color::Yellow)), Span::raw(" Backup "),
        Span::styled("[F3]", Style::default().fg(Color::Yellow)), Span::raw(" Restore "),
        Span::styled("[F4]", Style::default().fg(Color::Yellow)), Span::raw(" Snapshots "),
        Span::styled("[F6]", Style::default().fg(Color::Yellow)), Span::raw(" Settings "),
        Span::styled("[Q]", Style::default().fg(Color::Yellow)), Span::raw(" Quit "),
    ]))
    .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(Color::DarkGray)));
    frame.render_widget(footer, chunks[2]);
}

fn render_progress_panel(frame: &mut Frame, area: Rect, progress: &LiveProgress) {
    let phase_str = match progress.phase {
        BackupPhase::Scanning => "🔍 Scanning",
        BackupPhase::Chunking => "✂️  Chunking",
        BackupPhase::Compressing => "🗜️  Compressing",
        BackupPhase::Encrypting => "🔒 Encrypting",
        BackupPhase::Uploading => "⬆️  Uploading",
        BackupPhase::Verifying => "✅ Verifying",
        BackupPhase::Complete => "✓ Complete",
    };

    let progress_pct = progress.progress_percent();
    let gauge = Gauge::default()
        .gauge_style(Style::default().fg(Color::Cyan))
        .percent(progress_pct as u16)
        .label(format!("{:.1}%", progress_pct));
    
    let info = Paragraph::new(vec![
        Line::from(Span::styled(phase_str, Style::default().fg(Color::Cyan))),
        Line::from(format!("📄 Datei: {}", progress.current_file)),
        Line::from(format!("⚡ Speed: {:.1} MB/s", progress.speed_mbps)),
        Line::from(format!("📦 Chunks: {} ({} dedup)", progress.chunks_created, progress.chunks_deduplicated)),
        Line::from(match progress.eta_secs {
            Some(eta) => format!("⏱️  ETA: {}s", eta),
            None => "".to_string(),
        }),
    ]);

    let block = Block::default()
        .title(" Live Progress ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));

    let inner = block.inner(area);
    frame.render_widget(block, area);
    
    let gauge_area = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([Constraint::Length(1), Constraint::Min(5)])
        .split(inner);
    
    frame.render_widget(gauge, gauge_area[0]);
    frame.render_widget(info, gauge_area[1]);
}

fn render_status_panel(frame: &mut Frame, area: Rect, stats: &BackupStats) {
    let savings_pct = stats.savings_percentage() * 100.0;
    
    let status = Paragraph::new(vec![
        Line::from(Span::styled("📊 Statistik", Style::default().fg(Color::White).add_modifier(ratatui::style::Modifier::BOLD))),
        Line::from(""),
        Line::from(format!("📦 Backups: {} erfolgreich, {} fehlgeschlagen", stats.successful_backups, stats.failed_backups)),
        Line::from(format!("📁 Dateien: {}", stats.total_files)),
        Line::from(format!("💾 Gesamtgröße: {:.2} GB", stats.total_size as f64 / 1024.0 / 1024.0 / 1024.0)),
        Line::from(format!("🗜️  Komprimiert: {:.2} GB", stats.compressed_size as f64 / 1024.0 / 1024.0 / 1024.0)),
        Line::from(format!("♻️  Dedupliziert: {:.2} GB", stats.deduplicated_size as f64 / 1024.0 / 1024.0 / 1024.0)),
        Line::from(format!("💰 Ersparnis: {:.1}%", savings_pct)),
    ])
    .block(Block::default()
        .title(" Status ")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::White)));
    
    frame.render_widget(status, area);
}
