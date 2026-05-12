// src/core/merkle.rs - BLAKE3 Merkle Tree for Integrity Verification
use anyhow::Result;
use blake3::Hasher;

/// Merkle Tree node
#[derive(Debug, Clone)]
pub struct MerkleNode {
    pub hash: String,
    pub left: Option<Box<MerkleNode>>,
    pub right: Option<Box<MerkleNode>>,
    pub data_hash: Option<String>,
}

/// Merkle Tree for verifying backup integrity
pub struct MerkleTree {
    pub root: Option<MerkleNode>,
    pub leaves: Vec<String>,
}

impl MerkleTree {
    pub fn new() -> Self {
        Self {
            root: None,
            leaves: Vec::new(),
        }
    }

    /// Build tree from chunk hashes
    pub fn build(&mut self, chunk_hashes: &[String]) {
        if chunk_hashes.is_empty() {
            return;
        }

        self.leaves = chunk_hashes.to_vec();
        self.root = Some(self.build_tree(&self.leaves));
    }

    fn build_tree(&self, hashes: &[String]) -> MerkleNode {
        if hashes.len() == 1 {
            return MerkleNode {
                hash: hashes[0].clone(),
                left: None,
                right: None,
                data_hash: Some(hashes[0].clone()),
            };
        }

        let mid = hashes.len() / 2;
        let left = self.build_tree(&hashes[..mid]);
        let right = self.build_tree(&hashes[mid..]);

        let combined = format!("{}{}", left.hash, right.hash);
        let hash = blake3::hash(combined.as_bytes()).to_hex().to_string();

        MerkleNode {
            hash,
            left: Some(Box::new(left)),
            right: Some(Box::new(right)),
            data_hash: None,
        }
    }

    /// Get root hash
    pub fn root_hash(&self) -> Option<String> {
        self.root.as_ref().map(|n| n.hash.clone())
    }

    /// Verify a leaf is part of the tree
    pub fn verify(&self, leaf_hash: &str) -> bool {
        self.leaves.iter().any(|h| h == leaf_hash)
    }

    /// Generate proof for a leaf (for distributed verification)
    pub fn generate_proof(&self, leaf_index: usize) -> Vec<(String, Direction)> {
        let mut proof = Vec::new();
        let mut index = leaf_index;
        let mut level_size = self.leaves.len();
        
        let mut current_level: Vec<String> = self.leaves.clone();
        
        while current_level.len() > 1 {
            let next_level: Vec<String> = current_level
                .chunks(2)
                .map(|chunk| {
                    if chunk.len() == 2 {
                        let combined = format!("{}{}", chunk[0], chunk[1]);
                        blake3::hash(combined.as_bytes()).to_hex().to_string()
                    } else {
                        chunk[0].clone()
                    }
                })
                .collect();

            let sibling_index = if index % 2 == 0 { index + 1 } else { index - 1 };
            let direction = if index % 2 == 0 { Direction::Right } else { Direction::Left };
            
            if sibling_index < current_level.len() {
                proof.push((current_level[sibling_index].clone(), direction));
            }

            current_level = next_level;
            index /= 2;
            level_size /= 2;
        }

        proof
    }
}

#[derive(Debug, Clone, Copy)]
pub enum Direction {
    Left,
    Right,
}

impl Default for MerkleTree {
    fn default() -> Self {
        Self::new()
    }
}

/// Verify data integrity using Merkle proof
pub fn verify_merkle_proof(
    leaf_hash: &str,
    proof: &[(String, Direction)],
    expected_root: &str,
) -> bool {
    let mut current = leaf_hash.to_string();
    
    for (sibling, direction) in proof {
        let combined = match direction {
            Direction::Left => format!("{}{}", sibling, current),
            Direction::Right => format!("{}{}", current, sibling),
        };
        current = blake3::hash(combined.as_bytes()).to_hex().to_string();
    }
    
    current == expected_root
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_tree() {
        let hashes = vec![
            "a".to_string(),
            "b".to_string(),
            "c".to_string(),
            "d".to_string(),
        ];
        
        let mut tree = MerkleTree::new();
        tree.build(&hashes);
        
        assert!(tree.root.is_some());
        assert!(!tree.root_hash().unwrap().is_empty());
    }

    #[test]
    fn test_verify_leaf() {
        let hashes = vec!["x".to_string(), "y".to_string()];
        let mut tree = MerkleTree::new();
        tree.build(&hashes);
        
        assert!(tree.verify("x"));
        assert!(!tree.verify("z"));
    }
}
