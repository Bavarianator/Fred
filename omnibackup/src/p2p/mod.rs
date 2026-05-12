// src/p2p/mod.rs - P2P Backup mit libp2p
use anyhow::{Result, Context};
use libp2p::{
    core::transport::upgrade::Version,
    gossipsub::{self, Gossipsub, GossipsubConfig, GossipsubConfigBuilder, MessageAuthenticity, Topic},
    identity::{Keypair, ed25519},
    mplex::MplexConfig,
    noise,
    swarm::{NetworkBehaviour, SwarmEvent, SwarmBuilder},
    tcp, yamux, PeerId, Multiaddr,
    kad::{Kademlia, KademliaConfig, KademliaEvent, QueryResult, Quorum, RecordKey},
    mdns::{Mdns, MdnsEvent},
    relay,
    ping::{Ping, PingEvent},
};
use libp2p::swarm::behaviour::toggle::Toggle;
use tokio::sync::mpsc;
use bytes::Bytes;
use std::collections::{HashMap, HashSet};
use serde::{Serialize, Deserialize};
use crate::error::OmniError;

/// P2P Network Behaviour
#[derive(NetworkBehaviour)]
pub struct OmniBehaviour {
    pub gossipsub: Gossipsub,
    pub kademlia: Kademlia,
    pub mdns: Toggle<Mdns>,
    pub ping: Ping,
}

/// P2P Peer Information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerInfo {
    pub peer_id: String,
    pub multiaddr: Option<Multiaddr>,
    pub trust_level: TrustLevel,
    pub storage_offered: u64,
    pub storage_used: u64,
    pub last_seen: i64,
    pub protocols: Vec<String>,
}

/// Trust Level for Web-of-Trust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TrustLevel {
    Untrusted = 0,
    Low = 1,
    Medium = 2,
    High = 3,
    Trusted = 4,
}

/// Erasure Coding Configuration
#[derive(Debug, Clone)]
pub struct ErasureConfig {
    pub data_shards: usize,
    pub parity_shards: usize,
    pub shard_size: usize,
}

impl Default for ErasureConfig {
    fn default() -> Self {
        Self {
            data_shards: 3,
            parity_shards: 2,
            shard_size: 1024 * 1024, // 1MB
        }
    }
}

/// P2P Manager for decentralized backup
pub struct P2PManager {
    local_peer_id: PeerId,
    keypair: Keypair,
    known_peers: HashMap<String, PeerInfo>,
    trusted_peers: HashSet<String>,
    erasure_config: ErasureConfig,
    event_tx: mpsc::Sender<P2PEvent>,
    topics: Vec<Topic>,
}

/// P2P Events
#[derive(Debug, Clone)]
pub enum P2PEvent {
    PeerDiscovered(String),
    PeerConnected(String),
    PeerDisconnected(String),
    DataReceived { peer: String, chunk_id: String },
    DataSent { peer: String, chunk_id: String },
    StorageRequest { peer: String, size: u64 },
    Error(String),
}

impl P2PManager {
    /// Create new P2P manager
    pub async fn new(event_tx: mpsc::Sender<P2PEvent>) -> Result<Self> {
        let mut rng = rand::thread_rng();
        let keypair = Keypair::generate_ed25519(&mut rng);
        let local_peer_id = PeerId::from(keypair.public());
        
        log::info!("Local Peer ID: {}", local_peer_id);
        
        Ok(Self {
            local_peer_id,
            keypair,
            known_peers: HashMap::new(),
            trusted_peers: HashSet::new(),
            erasure_config: ErasureConfig::default(),
            event_tx,
            topics: Vec::new(),
        })
    }
    
    /// Start P2P network
    pub async fn start(&mut self, port: u16, enable_mdns: bool) -> Result<()> {
        use libp2p::Swarm;
        
        // Create transport
        let transport = tcp::tokio::Transport::new(tcp::Config::default())
            .upgrade(Version::V1)
            .authenticate(noise::Config::new(&self.keypair)?)
            .multiplex(yamux::Config::default())
            .boxed();
        
        // Create behaviour
        let mut gossipsub_config = GossipsubConfigBuilder::default()
            .heartbeat_interval(std::time::Duration::from_secs(10))
            .validation_mode(gossipsub::ValidationMode::Strict)
            .build()?;
        gossipsub_config.set_mesh_n(6);
        
        let message_authenticity = MessageAuthenticity::Signed(self.keypair.clone());
        let gossipsub = Gossipsub::new(message_authenticity, gossipsub_config)?;
        
        let mut kademlia_config = KademliaConfig::default();
        kademlia.set_query_timeout(std::time::Duration::from_secs(60));
        let store = libp2p::kad::record::store::MemoryStore::new(self.local_peer_id);
        let kademlia = Kademlia::with_config(self.local_peer_id, store, kademlia_config);
        
        let mdns = if enable_mdns {
            Some(Mdns::new(Default::default()).await?)
        } else {
            None
        }.into();
        
        let ping = Ping::default();
        
        let behaviour = OmniBehaviour {
            gossipsub,
            kademlia,
            mdns,
            ping,
        };
        
        let mut swarm = SwarmBuilder::with_tokio_executor(transport, behaviour, self.local_peer_id)
            .build();
        
        // Listen on all interfaces
        let listen_addr: Multiaddr = format!("/ip4/0.0.0.0/tcp/{}", port).parse()?;
        swarm.listen_on(listen_addr)?;
        
        log::info!("P2P listening on {}", listen_addr);
        
        // Subscribe to backup topic
        let backup_topic = Topic::new("omnibackup.v1");
        swarm.behaviour_mut().gossipsub.subscribe(&backup_topic)?;
        self.topics.push(backup_topic);
        
        // Event loop
        loop {
            tokio::select! {
                event = swarm.select_next_some() => {
                    match event {
                        SwarmEvent::NewListenAddr { address, .. } => {
                            log::info!("Listening on {}", address);
                        }
                        SwarmEvent::ConnectionEstablished { peer_id, endpoint, .. } => {
                            log::info!("Connected to {}", peer_id);
                            self.known_peers.insert(
                                peer_id.to_string(),
                                PeerInfo {
                                    peer_id: peer_id.to_string(),
                                    multiaddr: Some(endpoint.get_remote_address().clone()),
                                    trust_level: TrustLevel::Untrusted,
                                    storage_offered: 0,
                                    storage_used: 0,
                                    last_seen: chrono::Utc::now().timestamp(),
                                    protocols: vec![],
                                }
                            );
                            self.event_tx.send(P2PEvent::PeerConnected(peer_id.to_string())).await?;
                        }
                        SwarmEvent::ConnectionClosed { peer_id, .. } => {
                            log::info!("Disconnected from {}", peer_id);
                            self.event_tx.send(P2PEvent::PeerDisconnected(peer_id.to_string())).await?;
                        }
                        SwarmEvent::Behaviour(OmniBehaviourEvent::Gossipsub(
                            gossipsub::Event::Message { propagation_source: peer_id, message_id: id, message }
                        )) => {
                            log::info!(
                                "Got message: {} with data '{}' from peer: {}",
                                message_id,
                                String::from_utf8_lossy(&message.data),
                                peer_id,
                            );
                        }
                        SwarmEvent::Behaviour(OmniBehaviourEvent::Mdns(MdnsEvent::Discovered(list))) => {
                            for (peer_id, addr) in list {
                                log::info!("mDNS discovered {} {}", peer_id, addr);
                                self.event_tx.send(P2PEvent::PeerDiscovered(peer_id.to_string())).await?;
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
    }
    
    /// Add trusted peer
    pub fn add_trusted_peer(&mut self, peer_id: &str, multiaddr: Option<&str>) -> Result<()> {
        let mut peer_info = self.known_peers.entry(peer_id.to_string())
            .or_insert_with(|| PeerInfo {
                peer_id: peer_id.to_string(),
                multiaddr: None,
                trust_level: TrustLevel::Untrusted,
                storage_offered: 0,
                storage_used: 0,
                last_seen: chrono::Utc::now().timestamp(),
                protocols: vec![],
            });
        
        if let Some(addr) = multiaddr {
            peer_info.multiaddr = Some(addr.parse()?);
        }
        
        peer_info.trust_level = TrustLevel::Trusted;
        self.trusted_peers.insert(peer_id.to_string());
        
        log::info!("Added trusted peer: {}", peer_id);
        Ok(())
    }
    
    /// Encode data with Reed-Solomon erasure coding
    pub fn encode_erasure(&self, data: &[u8]) -> Result<Vec<Bytes>> {
        use reed_solomon_erasure::galois_8::Field;
        
        let total_shards = self.erasure_config.data_shards + self.erasure_config.parity_shards;
        let shard_size = self.erasure_config.shard_size;
        
        // Pad data to fit shards
        let padded_len = ((data.len() + shard_size - 1) / shard_size) * shard_size;
        let mut padded = data.to_vec();
        padded.resize(padded_len, 0);
        
        // Split into data shards
        let mut shards: Vec<Vec<u8>> = padded
            .chunks(shard_size)
            .map(|chunk| chunk.to_vec())
            .collect();
        
        // Add parity shards
        let field = Field::new();
        for _ in 0..self.erasure_config.parity_shards {
            shards.push(vec![0u8; shard_size]);
        }
        
        // Encode
        field.encode(&mut shards, self.erasure_config.data_shards)?;
        
        Ok(shards.into_iter().map(Bytes::from).collect())
    }
    
    /// Decode data from erasure-coded shards
    pub fn decode_erasure(&self, mut shards: Vec<Bytes>) -> Result<Bytes> {
        use reed_solomon_erasure::galois_8::Field;
        
        let field = Field::new();
        let data_shard_count = self.erasure_config.data_shards;
        
        // Decode
        field.decode(&mut shards, data_shard_count)?;
        
        // Combine data shards
        let mut result = Vec::new();
        for shard in shards.into_iter().take(data_shard_count) {
            result.extend_from_slice(&shard);
        }
        
        // Remove padding
        let actual_len = result.iter().rposition(|&x| x != 0).map(|i| i + 1).unwrap_or(0);
        result.truncate(actual_len);
        
        Ok(Bytes::from(result))
    }
    
    /// Get status
    pub fn status(&self) -> P2PStatus {
        P2PStatus {
            local_peer_id: self.local_peer_id.to_string(),
            connected_peers: self.known_peers.len(),
            trusted_peers: self.trusted_peers.len(),
            erasure_config: self.erasure_config.clone(),
        }
    }
}

/// P2P Status
#[derive(Debug, Serialize, Deserialize)]
pub struct P2PStatus {
    pub local_peer_id: String,
    pub connected_peers: usize,
    pub trusted_peers: usize,
    pub erasure_config: ErasureConfig,
}

pub fn placeholder() -> &'static str {
    "P2P module loaded"
}
