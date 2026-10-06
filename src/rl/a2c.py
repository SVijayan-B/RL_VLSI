"""
Phase 11: Advantage Actor-Critic (A2C) Network Architecture.
Implements:
- Actor Network: 41 -> 128 -> 128 -> 8 (Categorical Action Distribution)
- Critic Network: 41 -> 128 -> 128 -> 1 (State Value V(s))
- Loss: L = L_policy + 0.5 * L_value - 0.01 * Entropy
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

class ActorCritic(nn.Module):
    """
    Standard A2C Policy and Value Network.
    Follows recommended 41 -> 128 -> 128 -> 8 (Actor) and 41 -> 128 -> 128 -> 1 (Critic).
    """
    def __init__(self, state_dim: int = 41, action_dim: int = 8, hidden_dim: int = 128):
        super(ActorCritic, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Separate actor network (41 -> 128 -> 128 -> 8)
        self.actor_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

        # Separate critic network (41 -> 128 -> 128 -> 1)
        self.critic_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, state: torch.Tensor):
        """
        Returns:
            action_logits: [batch, action_dim]
            state_value: [batch, 1]
        """
        logits = self.actor_net(state)
        value = self.critic_net(state)
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
