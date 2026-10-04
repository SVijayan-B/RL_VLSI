#!/usr/bin/env python3
"""
GraphSAGE Architecture for Heterogeneous Netlist Cell Graph Representation
Project: Parameter Optimization of VLSI Placement Through Deep RL
Reference: Anthony Agnesina, Kyungwook Chang, Sung Kyu Lim, IEEE TCAD 2023

Architecture:
- Input dimension: 7 (Canonical standard cell features)
- Layer 1: SAGEConv(7 -> 64), ReLU, Dropout(0.20)
- Layer 2: SAGEConv(64 -> 32), ReLU
- Node Embeddings: [N, 32]
- Permutation-Invariant Graph Embedding: mean_pool(H) -> [32]
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class SAGEConvMean(nn.Module):
    """
    Genuine GraphSAGE Convolution Layer with Mean Neighborhood Aggregation.
    h_v = W_self * h_v + W_neigh * mean_{u in N(v)}(h_u) + bias
    Handles variable graph sizes, arbitrary degree distributions, and isolated nodes.
    """
    def __init__(self, in_features, out_features, bias=True):
        super(SAGEConvMean, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        
        self.lin_self = nn.Linear(in_features, out_features, bias=False)
        self.lin_neigh = nn.Linear(in_features, out_features, bias=False)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_parameter('bias', None)
            
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.lin_self.weight, a=math.sqrt(5))
        nn.init.kaiming_uniform_(self.lin_neigh.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.lin_self.weight)
            bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, x, edge_index):
        """
        x: [N, in_features]
        edge_index: [2, E] (undirected cell-to-cell projected edges)
        """
        N = x.size(0)
        E = edge_index.size(1)
        
        # Self transformation
        out = self.lin_self(x)
        
        if E > 0:
            src = edge_index[0] # neighbor node
            dst = edge_index[1] # target node to aggregate into
            
            # Neighborhood messages: x[src] -> shape [E, in_features]
            neigh_msgs = x[src]
            
            # Aggregate neighborhood sum via scatter_add
            # Create zeros tensor on same device
            neigh_sum = torch.zeros(N, self.in_features, device=x.device, dtype=x.dtype)
            neigh_sum.index_add_(0, dst, neigh_msgs)
            
            # Count degree of each node in dst
            deg = torch.zeros(N, 1, device=x.device, dtype=x.dtype)
            deg.index_add_(0, dst, torch.ones(E, 1, device=x.device, dtype=x.dtype))
            
            # Safe division: where deg > 0, compute mean; otherwise 0
            mask = deg > 0
            neigh_mean = torch.zeros_like(neigh_sum)
            neigh_mean[mask.squeeze(1)] = neigh_sum[mask.squeeze(1)] / deg[mask.squeeze(1)]
            
            out = out + self.lin_neigh(neigh_mean)
        else:
            # If graph has no edges, use self only
            pass
            
        if self.bias is not None:
            out = out + self.bias
            
        return out


class NetlistGraphSAGE(nn.Module):
    """
    2-Layer GraphSAGE Network for VLSI Netlists
    d_in = 7 -> d_hidden = 64 -> d_out = 32
    """
    def __init__(self, in_dim=7, hidden_dim=64, out_dim=32, dropout=0.20):
        super(NetlistGraphSAGE, self).__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.dropout_rate = dropout
        
        self.conv1 = SAGEConvMean(in_dim, hidden_dim)
        self.conv2 = SAGEConvMean(hidden_dim, out_dim)

    def forward(self, x, edge_index):
        """
        x: [N, 7]
        edge_index: [2, E]
        Returns:
            h_nodes: [N, 32] (Node embeddings)
            h_graph: [32] (Permutation-invariant mean aggregated graph embedding)
        """
        # Layer 1
        h = self.conv1(x, edge_index)
        h = F.relu(h)
        if self.dropout_rate > 0.0 and self.training:
            h = F.dropout(h, p=self.dropout_rate, training=True)
            
        # Layer 2
        h_nodes = self.conv2(h, edge_index)
        h_nodes = F.relu(h_nodes)
        
        # Permutation-invariant mean aggregation across all N cell nodes
        h_graph = torch.mean(h_nodes, dim=0)
        
        return h_nodes, h_graph


class InfoNCELoss(nn.Module):
    """
    Unsupervised InfoNCE Contrastive Loss for GraphSAGE
    Maximizes mutual information between connected node pairs (positives)
    relative to K randomly sampled negative node pairs.
    L = -log( exp(sim(u, v) / T) / ( exp(sim(u, v) / T) + sum_{k=1}^K exp(sim(u, n_k) / T) ) )
    """
    def __init__(self, temperature=0.5, negative_samples=10):
        super(InfoNCELoss, self).__init__()
        self.temperature = temperature
        self.k = negative_samples

    def forward(self, h_nodes, edge_index, max_batch_edges=20000):
        """
        h_nodes: [N, 32]
        edge_index: [2, E]
        max_batch_edges: Subsamples edges per step if E is massive to ensure memory safety
        """
        N = h_nodes.size(0)
        E = edge_index.size(1)
        if E == 0:
            return torch.tensor(0.0, device=h_nodes.device, requires_grad=True)

        # L2 Normalize embeddings for cosine similarity
        h_norm = F.normalize(h_nodes, p=2, dim=1)

        # Subsample edges if needed to fit GPU cache
        if E > max_batch_edges:
            perm = torch.randperm(E, device=h_nodes.device)[:max_batch_edges]
            u = edge_index[0, perm]
            v = edge_index[1, perm]
            batch_e = max_batch_edges
        else:
            u = edge_index[0]
            v = edge_index[1]
            batch_e = E

        # Positive pair similarity: [B]
        pos_sim = torch.sum(h_norm[u] * h_norm[v], dim=1) / self.temperature

        # Negative sampling: sample K random negative nodes for each positive pair
        # Negatives shape: [B, K]
        neg_indices = torch.randint(0, N, (batch_e, self.k), device=h_nodes.device)
        # Gather negative embeddings: [B, K, 32]
        neg_embeds = h_norm[neg_indices]
        # Compute negative similarities: [B, K]
        u_embeds = h_norm[u].unsqueeze(1) # [B, 1, 32]
        neg_sim = torch.sum(u_embeds * neg_embeds, dim=2) / self.temperature

        # InfoNCE denominator: log-sum-exp over positive and K negatives
        # Concatenate pos [B, 1] and neg [B, K] -> [B, 1 + K]
        logits = torch.cat([pos_sim.unsqueeze(1), neg_sim], dim=1)
        labels = torch.zeros(batch_e, dtype=torch.long, device=h_nodes.device) # positive is at index 0

        loss = F.cross_entropy(logits, labels)
        return loss

if __name__ == '__main__':
    # Unit test smoke check
    model = NetlistGraphSAGE(in_dim=7, hidden_dim=64, out_dim=32)
    criterion = InfoNCELoss()
    x = torch.randn(100, 7)
    edge_index = torch.randint(0, 100, (2, 300))
    h_nodes, h_graph = model(x, edge_index)
    loss = criterion(h_nodes, edge_index)
    print("GraphSAGE Self-Test:")
    print("  Node embeddings:", h_nodes.shape)
    print("  Graph embedding:", h_graph.shape)
    print("  InfoNCE Loss   :", loss.item())
