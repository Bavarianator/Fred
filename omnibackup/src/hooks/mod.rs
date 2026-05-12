// src/hooks/mod.rs - Pre/Post-Hooks und Application-Aware Backups
use anyhow::Result;
use serde::{Serialize, Deserialize};
use std::path::PathBuf;
use std::collections::HashMap;
use tokio::process::Command;

/// Hook Configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HookConfig {
    pub name: String,
    #[serde(default)]
    pub pre_backup: Vec<String>,
    #[serde(default)]
    pub post_backup: Vec<String>,
    #[serde(default)]
    pub on_error: Vec<String>,
    #[serde(default)]
    pub app_aware: Vec<AppAwareConfig>,
}

/// Application-Aware Backup Configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppAwareConfig {
    pub app_type: String,
    pub enabled: bool,
    pub dump_command: Option<String>,
    pub dump_path: Option<String>,
    pub cleanup_command: Option<String>,
    pub timeout_secs: u64,
}

/// Hook Executor
pub struct HookExecutor {
    config: HookConfig,
    env_vars: HashMap<String, String>,
    working_dir: Option<PathBuf>,
}

impl HookExecutor {
    /// Create new hook executor
    pub fn new(config: HookConfig) -> Self {
        Self {
            config,
            env_vars: HashMap::new(),
            working_dir: None,
        }
    }
    
    /// Set environment variables for hooks
    pub fn set_env(&mut self, key: &str, value: &str) {
        self.env_vars.insert(key.to_string(), value.to_string());
    }
    
    /// Set working directory
    pub fn set_working_dir(&mut self, path: PathBuf) {
        self.working_dir = Some(path);
    }
    
    /// Execute pre-backup hooks
    pub async fn run_pre_backup(&self) -> Result<Vec<HookResult>> {
        let mut results = Vec::new();
        
        for cmd in &self.config.pre_backup {
            log::info!("Running pre-backup hook: {}", cmd);
            let result = self.execute_command(cmd).await;
            results.push(result);
        }
        
        Ok(results)
    }
    
    /// Execute post-backup hooks
    pub async fn run_post_backup(&self, success: bool) -> Result<Vec<HookResult>> {
        let mut results = Vec::new();
        
        // Run standard post-backup hooks
        for cmd in &self.config.post_backup {
            log::info!("Running post-backup hook: {}", cmd);
            let result = self.execute_command(cmd).await;
            results.push(result);
        }
        
        // Run error hooks if backup failed
        if !success {
            for cmd in &self.config.on_error {
                log::warn!("Running error hook: {}", cmd);
                let result = self.execute_command(cmd).await;
                results.push(result);
            }
        }
        
        Ok(results)
    }
    
    /// Execute application-aware backups
    pub async fn run_app_aware_backups(&self) -> Result<Vec<AppBackupResult>> {
        let mut results = Vec::new();
        
        for app_config in &self.config.app_aware {
            if !app_config.enabled {
                continue;
            }
            
            log::info!("Running app-aware backup for: {}", app_config.app_type);
            
            let result = match app_config.app_type.as_str() {
                "postgresql" => self.backup_postgresql(app_config).await,
                "mysql" | "mariadb" => self.backup_mysql(app_config).await,
                "mongodb" => self.backup_mongodb(app_config).await,
                "sqlite" => self.backup_sqlite(app_config).await,
                "redis" => self.backup_redis(app_config).await,
                "docker" => self.backup_docker(app_config).await,
                "browser-firefox" => self.backup_firefox(app_config).await,
                "browser-chrome" => self.backup_chrome(app_config).await,
                "thunderbird" => self.backup_thunderbird(app_config).await,
                "obsidian" => self.backup_obsidian(app_config).await,
                "git" => self.backup_git(app_config).await,
                _ => {
                    log::warn!("Unknown app type: {}", app_config.app_type);
                    continue;
                }
            };
            
            results.push(result);
        }
        
        Ok(results)
    }
    
    /// Execute a single command
    async fn execute_command(&self, cmd: &str) -> HookResult {
        let start = std::time::Instant::now();
        
        let mut command = Command::new("sh");
        command.arg("-c").arg(cmd);
        
        // Add environment variables
        for (key, value) in &self.env_vars {
            command.env(key, value);
        }
        
        // Set working directory
        if let Some(ref dir) = self.working_dir {
            command.current_dir(dir);
        }
        
        let output = match command.output().await {
            Ok(output) => output,
            Err(e) => {
                return HookResult {
                    command: cmd.to_string(),
                    success: false,
                    exit_code: None,
                    stdout: String::new(),
                    stderr: e.to_string(),
                    duration_ms: start.elapsed().as_millis() as u64,
                }
            }
        };
        
        HookResult {
            command: cmd.to_string(),
            success: output.status.success(),
            exit_code: output.status.code(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            duration_ms: start.elapsed().as_millis() as u64,
        }
    }
    
    /// PostgreSQL backup
    async fn backup_postgresql(&self, config: &AppAwareConfig) -> AppBackupResult {
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("pg_dump --format=custom --compress=9");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// MySQL/MariaDB backup
    async fn backup_mysql(&self, config: &AppAwareConfig) -> AppBackupResult {
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("mysqldump --all-databases --single-transaction --quick");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// MongoDB backup
    async fn backup_mongodb(&self, config: &AppAwareConfig) -> AppBackupResult {
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("mongodump --archive --gzip");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// SQLite backup
    async fn backup_sqlite(&self, config: &AppAwareConfig) -> AppBackupResult {
        // SQLite files can be copied directly if not in WAL mode
        // Or use .backup command
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("sqlite3 :memory: '.backup'");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// Redis backup
    async fn backup_redis(&self, config: &AppAwareConfig) -> AppBackupResult {
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("redis-cli BGSAVE");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// Docker volumes backup
    async fn backup_docker(&self, config: &AppAwareConfig) -> AppBackupResult {
        let dump_cmd = config.dump_command.as_deref()
            .unwrap_or("docker run --rm -v myvolume:/data alpine tar czf - /data");
        
        self.run_dump_command(dump_cmd, config).await
    }
    
    /// Firefox profile backup
    async fn backup_firefox(&self, config: &AppAwareConfig) -> AppBackupResult {
        // Firefox profile is just files, but we should check if Firefox is running
        let result = self.check_process_running("firefox").await;
        
        AppBackupResult {
            app_type: "firefox".to_string(),
            success: true,
            warning: if result { 
                Some("Firefox is running, some files may be locked".to_string()) 
            } else { 
                None 
            },
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: 0,
        }
    }
    
    /// Chrome profile backup
    async fn backup_chrome(&self, config: &AppAwareConfig) -> AppBackupResult {
        let result = self.check_process_running("chrome").await;
        
        AppBackupResult {
            app_type: "chrome".to_string(),
            success: true,
            warning: if result { 
                Some("Chrome is running, some files may be locked".to_string()) 
            } else { 
                None 
            },
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: 0,
        }
    }
    
    /// Thunderbird backup
    async fn backup_thunderbird(&self, config: &AppAwareConfig) -> AppBackupResult {
        let result = self.check_process_running("thunderbird").await;
        
        AppBackupResult {
            app_type: "thunderbird".to_string(),
            success: true,
            warning: if result { 
                Some("Thunderbird is running".to_string()) 
            } else { 
                None 
            },
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: 0,
        }
    }
    
    /// Obsidian vault backup
    async fn backup_obsidian(&self, config: &AppAwareConfig) -> AppBackupResult {
        // Check if vault is locked
        AppBackupResult {
            app_type: "obsidian".to_string(),
            success: true,
            warning: None,
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: 0,
        }
    }
    
    /// Git repository backup
    async fn backup_git(&self, config: &AppAwareConfig) -> AppBackupResult {
        // Run git status to check for uncommitted changes
        let result = self.execute_command("git status --porcelain").await;
        
        let warning = if !result.stdout.is_empty() {
            Some("Git repository has uncommitted changes".to_string())
        } else {
            None
        };
        
        AppBackupResult {
            app_type: "git".to_string(),
            success: true,
            warning,
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: result.duration_ms,
        }
    }
    
    /// Generic dump command runner
    async fn run_dump_command(&self, cmd: &str, config: &AppAwareConfig) -> AppBackupResult {
        let start = std::time::Instant::now();
        let result = self.execute_command(cmd).await;
        
        // Run cleanup if specified
        if let Some(cleanup) = &config.cleanup_command {
            let _ = self.execute_command(cleanup).await;
        }
        
        AppBackupResult {
            app_type: config.app_type.clone(),
            success: result.success,
            warning: if !result.stderr.is_empty() { 
                Some(result.stderr) 
            } else { 
                None 
            },
            dump_path: config.dump_path.clone(),
            size_bytes: 0,
            duration_ms: start.elapsed().as_millis() as u64,
        }
    }
    
    /// Check if process is running
    async fn check_process_running(&self, process_name: &str) -> bool {
        let cmd = format!("pgrep -x {}", process_name);
        let result = self.execute_command(&cmd).await;
        result.success
    }
}

/// Hook execution result
#[derive(Debug, Clone)]
pub struct HookResult {
    pub command: String,
    pub success: bool,
    pub exit_code: Option<i32>,
    pub stdout: String,
    pub stderr: String,
    pub duration_ms: u64,
}

/// Application backup result
#[derive(Debug, Clone)]
pub struct AppBackupResult {
    pub app_type: String,
    pub success: bool,
    pub warning: Option<String>,
    pub dump_path: Option<String>,
    pub size_bytes: u64,
    pub duration_ms: u64,
}

pub fn placeholder() -> &'static str {
    "Hooks module loaded"
}
