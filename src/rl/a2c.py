"""
Phase 10: Advantage Actor-Critic (A2C) Network Architecture.
Implements:
- Shared or separate MLP state representation
- Actor Head: state (41) -> hidden (64) -> action distribution (8)
- Critic Head: state (41) -> hidden (64) -> state value V(s) (1)
- Loss: L = L_policy + 0.5 * L_value - 0.01 * Entropy
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

class ActorCritic(nn.Module):
    """
    Standard A2C Policy and Value Network.
    """
    def __init__(self, state_dim: int = 41, action_dim: int = 8, hidden_dim: int = 64):
        super(ActorCritic, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Feature extractor
        self.fc_shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )

        # Actor head (action logits)
        self.actor_head = nn.Linear(hidden_dim, action_dim)

        # Critic head (state value)
        self.critic_head = nn.Linear(hidden_dim, 1)

    def forward(self, state: torch.Tensor):
        """
        Returns:
            action_logits: [batch, action_dim]
            state_value: [batch, 1]
        """
        feat = self.fc_shared(state)
        logits = self.actor_head(feat)
        value = self.critic_head(feat)
        return logits, value

    def get_action_and_value(self, state: torch.Tensor, action: torch.Tensor = None):
        """
        Samples action from policy or evaluates log prob of provided action.
        """
        logits, value = self.forward(state)
        dist = Categorical(logits=logits)

        if action is None:
            action = dist.sample()

        log_prob = dist.log_prob(action)
        entropy = dist.entropy()

        return action, log_prob, entropy, value
