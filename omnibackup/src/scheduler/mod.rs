// src/scheduler/mod.rs - Scheduler mit Cron, FS-Watcher und Triggers
use anyhow::Result;
use chrono::{DateTime, Local, NaiveTime};
use cron::Schedule;
use std::path::PathBuf;
use tokio::sync::mpsc;
use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher, EventKind};
use serde::{Serialize, Deserialize};
use std::time::Duration;
use crate::config::BackupSchedule;

/// Scheduler Event
#[derive(Debug, Clone)]
pub enum SchedulerEvent {
    BackupTriggered(String),  // schedule_name
    UsbDriveDetected(PathBuf),
    IdleDetected,
    NetworkAvailable,
    LowBattery,
    Error(String),
}

/// Scheduler Manager
pub struct SchedulerManager {
    schedules: Vec<ScheduledTask>,
    watcher: Option<RecommendedWatcher>,
    event_tx: mpsc::Sender<SchedulerEvent>,
    running: bool,
    watched_paths: Vec<PathBuf>,
    idle_threshold: Duration,
    bandwidth_limited: bool,
}

/// Scheduled Task
#[derive(Debug, Clone)]
pub struct ScheduledTask {
    pub name: String,
    pub schedule: ScheduleType,
    pub enabled: bool,
    pub last_run: Option<DateTime<Local>>,
    pub next_run: Option<DateTime<Local>>,
    pub sources: Vec<PathBuf>,
    pub destinations: Vec<String>,
}

/// Schedule Type
#[derive(Debug, Clone)]
pub enum ScheduleType {
    Cron(Schedule),
    Hourly,
    Daily(NaiveTime),
    Weekly(u32, NaiveTime),  // weekday, time
    Monthly(u32, NaiveTime), // day, time
    Continuous(Duration),    // interval
    Manual,
}

impl SchedulerManager {
    /// Create new scheduler
    pub fn new(event_tx: mpsc::Sender<SchedulerEvent>) -> Self {
        Self {
            schedules: Vec::new(),
            watcher: None,
            event_tx,
            running: false,
            watched_paths: Vec::new(),
            idle_threshold: Duration::from_secs(300), // 5 minutes
            bandwidth_limited: false,
        }
    }
    
    /// Add schedule from config
    pub fn add_schedule(&mut self, schedule: &BackupSchedule) -> Result<()> {
        let schedule_type = match &schedule.r#type[..] {
            "hourly" => ScheduleType::Hourly,
            "daily" => {
                let time = NaiveTime::parse_from_str(&schedule.time.as_deref().unwrap_or("02:00"), "%H:%M")?;
                ScheduleType::Daily(time)
            }
            "weekly" => {
                let weekday = schedule.weekday.unwrap_or(0);
                let time = NaiveTime::parse_from_str(&schedule.time.as_deref().unwrap_or("02:00"), "%H:%M")?;
                ScheduleType::Weekly(weekday, time)
            }
            "monthly" => {
                let day = schedule.day.unwrap_or(1);
                let time = NaiveTime::parse_from_str(&schedule.time.as_deref().unwrap_or("02:00"), "%H:%M")?;
                ScheduleType::Monthly(day, time)
            }
            "continuous" => {
                let interval_secs = schedule.interval_secs.unwrap_or(900); // 15 min
                ScheduleType::Continuous(Duration::from_secs(interval_secs))
            }
            "manual" | _ => ScheduleType::Manual,
        };
        
        let task = ScheduledTask {
            name: schedule.name.clone(),
            schedule: schedule_type,
            enabled: schedule.enabled.unwrap_or(true),
            last_run: None,
            next_run: None,
            sources: schedule.sources.iter().map(PathBuf::from).collect(),
            destinations: schedule.destinations.clone(),
        };
        
        self.schedules.push(task);
        log::info!("Added schedule: {}", schedule.name);
        Ok(())
    }
    
    /// Start file system watcher for continuous backup
    pub fn start_watcher(&mut self, paths: &[PathBuf]) -> Result<()> {
        let tx = self.event_tx.clone();
        
        let mut watcher = RecommendedWatcher::new(
            move |res: notify::Result<notify::Event>| {
                if let Ok(event) = res {
                    if matches!(event.kind, EventKind::Modify(_) | EventKind::Create(_)) {
                        for path in event.paths {
                            log::info!("File changed: {:?}", path);
                            // Debounce could be added here
                        }
                    }
                }
            },
            Config::default(),
        )?;
        
        for path in paths {
            if path.exists() {
                watcher.watch(path, RecursiveMode::Recursive)?;
                log::info!("Watching: {:?}", path);
                self.watched_paths.push(path.clone());
            }
        }
        
        self.watcher = Some(watcher);
        Ok(())
    }
    
    /// Run scheduler main loop
    pub async fn run(&mut self) -> Result<()> {
        self.running = true;
        let mut interval = tokio::time::interval(Duration::from_secs(60));
        
        while self.running {
            interval.tick().await;
            
            let now = Local::now();
            
            for task in &mut self.schedules {
                if !task.enabled {
                    continue;
                }
                
                let should_run = match &task.schedule {
                    ScheduleType::Cron(schedule) => {
                        schedule.upcoming(Local).next() <= Some(now)
                    }
                    ScheduleType::Hourly => {
                        task.last_run.map_or(true, |last| {
                            now.signed_duration_since(last) > chrono::Duration::hours(1)
                        })
                    }
                    ScheduleType::Daily(time) => {
                        let today = now.date_naive().and_time(*time);
                        today.map_or(false, |dt| {
                            let dt_local = Local.from_utc_datetime(&dt);
                            task.last_run.map_or(true, |last| dt_local > last)
                        })
                    }
                    ScheduleType::Weekly(weekday, time) => {
                        if now.weekday().num_days_from_monday() == *weekday {
                            let today = now.date_naive().and_time(*time);
                            today.map_or(false, |dt| {
                                let dt_local = Local.from_utc_datetime(&dt);
                                task.last_run.map_or(true, |last| dt_local > last)
                            })
                        } else {
                            false
                        }
                    }
                    ScheduleType::Monthly(day, time) => {
                        if now.day() == *day {
                            let today = now.date_naive().and_time(*time);
                            today.map_or(false, |dt| {
                                let dt_local = Local.from_utc_datetime(&dt);
                                task.last_run.map_or(true, |last| dt_local > last)
                            })
                        } else {
                            false
                        }
                    }
                    ScheduleType::Continuous(duration) => {
                        task.last_run.map_or(true, |last| {
                            now.signed_duration_since(last) > chrono::Duration::from_std(*duration).unwrap()
                        })
                    }
                    ScheduleType::Manual => false,
                };
                
                if should_run {
                    log::info!("Triggering backup: {}", task.name);
                    self.event_tx.send(SchedulerEvent::BackupTriggered(task.name.clone())).await?;
                    task.last_run = Some(now);
                }
                
                // Calculate next run
                task.next_run = match &task.schedule {
                    ScheduleType::Cron(schedule) => schedule.upcoming(Local).next(),
                    ScheduleType::Hourly => {
                        Some(now + chrono::Duration::hours(1))
                    }
                    ScheduleType::Daily(time) => {
                        let today = now.date_naive().and_time(*time);
                        today.map(|dt| Local.from_utc_datetime(&dt))
                    }
                    _ => None,
                };
            }
        }
        
        Ok(())
    }
    
    /// Trigger manual backup
    pub fn trigger_now(&self, schedule_name: &str) -> Result<()> {
        let tx = self.event_tx.clone();
        let name = schedule_name.to_string();
        
        tokio::spawn(async move {
            if let Err(e) = tx.send(SchedulerEvent::BackupTriggered(name)).await {
                log::error!("Failed to send trigger: {}", e);
            }
        });
        
        Ok(())
    }
    
    /// Get status
    pub fn status(&self) -> SchedulerStatus {
        SchedulerStatus {
            running: self.running,
            schedules_count: self.schedules.len(),
            watched_paths: self.watched_paths.len(),
            bandwidth_limited: self.bandwidth_limited,
        }
    }
    
    /// Stop scheduler
    pub fn stop(&mut self) {
        self.running = false;
        self.watcher = None;
    }
}

/// Scheduler Status
#[derive(Debug, Serialize, Deserialize)]
pub struct SchedulerStatus {
    pub running: bool,
    pub schedules_count: usize,
    pub watched_paths: usize,
    pub bandwidth_limited: bool,
}

pub fn placeholder() -> &'static str {
    "Scheduler module loaded"
}
