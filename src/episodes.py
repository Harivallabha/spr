import torch
import numpy as np
from collections import deque, namedtuple
from itertools import chain


from src.memory import blank_batch_trans as blank_trans
from src.envs import Env, AARIEnv

Transition = namedtuple('Transition', ('timestep', 'state', 'action', 'reward', 'nonterminal'))


def get_random_agent_episodes(args):
    env = Env(args)
    env.train()
    action_space = env.action_space()
    print('-------Collecting samples----------')
    transitions = []
    timestep, done = 0, True
    for T in range(args.initial_exp_steps):
        if done:
            state, done = env.reset(), False
        state = state[-1].mul(255).to(dtype=torch.uint8,
                                      device=torch.device('cpu'))  # Only store last frame and discretise to save memory
        action = np.random.randint(0, action_space)
        next_state, reward, done = env.step(action)
        if args.reward_clip > 0:
            reward = max(min(reward, args.reward_clip), -args.reward_clip)  # Clip rewards
        transitions.append(Transition(timestep, state, action, reward, not done))
        state = next_state
        timestep = 0 if done else timestep + 1

    env.close()
    return transitions


def sample_real_transitions(real_transitions, num_samples):
    samples = []
    actions = np.zeros((num_samples, 4))
    rewards = np.zeros((num_samples, 4))
    for i in range(num_samples):
        idx = np.random.randint(0, len(real_transitions))
        states = []
        for k, trans in enumerate(get_framestacked_transition(idx, real_transitions)):
            states.append(trans.state.float() / 255.)
            actions[i, k] = trans.action
            rewards[i, k] = trans.reward
        samples.append(torch.stack(states))
    return torch.stack(samples), torch.tensor(actions).long(), torch.tensor(rewards).long()


def get_framestacked_transition(idx, transitions):
    history = 4
    transition = np.array([None] * history)
    transition[history - 1] = transitions[idx]
    for t in range(4 - 2, -1, -1):  # e.g. 2 1 0
        if transition[t + 1].timestep == 0:
            transition[t] = blank_trans  # If future frame has timestep 0
        else:
            transition[t] = transitions[idx - history + 1 + t]
    return transition


def get_labeled_rollouts(args):
    env = AARIEnv(args)
    env.train()
    action_space = env.action_space()
    print('-------Collecting samples----------')
    transitions = []
    labels = []
    timestep, done = 0, True
    for T in range(args.initial_exp_steps):
        if done:
            state, done = env.reset(), False
        state = state[-1].mul(255).to(dtype=torch.uint8,
                                      device=torch.device('cpu'))  # Only store last frame and discretise to save memory
        action = np.random.randint(0, action_space)
        next_state, reward, done, info = env.step(action)
        if args.reward_clip > 0:
            reward = max(min(reward, args.reward_clip), -args.reward_clip)  # Clip rewards
        transitions.append(Transition(timestep, state, action, reward, not done))
        state = next_state
        timestep = 0 if done else timestep + 1
        if "labels" in info.keys():
            labels.append(info["labels"])

    env.close()
    return transitions, labels

def remove_low_entropy_labels(episode_labels, entropy_threshold=0.3):
    flat_label_list = list(chain.from_iterable(episode_labels))
    counts = {}

    for label_dict in flat_label_list:
        for k in label_dict:
            counts[k] = counts.get(k, {})
            v = label_dict[k]
            counts[k][v] = counts[k].get(v, 0) + 1
    low_entropy_labels = []

    entropy_dict = {}
    for k in counts:
        entropy = torch.distributions.Categorical(
            torch.tensor([x / len(flat_label_list) for x in counts[k].values()])).entropy()
        entropy_dict['entropy_' + k] = entropy
        if entropy < entropy_threshold:
            print("Deleting {} for being too low in entropy! Sorry, dood!".format(k))
            low_entropy_labels.append(k)

    for e in episode_labels:
        for obs in e:
            for key in low_entropy_labels:
                del obs[key]
    # wandb.log(entropy_dict)
    return episode_labels, entropy_dict


def get_labeled_episodes(args,
                         entropy_threshold=0.6,):

        # List of episodes. Each episode is a list of 160x210 observations
        train_transitions, train_labels = get_labeled_rollouts(args)
        val_transitions, val_labels = get_labeled_rollouts(args)
        test_transitions, test_labels = get_labeled_rollouts(args)

        all_labels = [train_labels, val_labels, test_labels]
        all_labels, entropy_dict = remove_low_entropy_labels(all_labels,
                                                             entropy_threshold=entropy_threshold)
        train_labels, val_labels, test_labels = all_labels


        return train_transitions, train_labels,\
               val_transitions, val_labels, \
               test_transitions, test_labels