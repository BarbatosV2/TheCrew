import os
import argparse

import torch

import rlcard
from rlcard.agents import RandomAgent
from rlcard.utils import get_device, set_seed, tournament, reorganize, Logger


def train(args):
    # Check whether gpu is available
    device = get_device()

    # Seed numpy, torch, random
    set_seed(args.seed)

    # Make the environment with seed
    env = rlcard.make(args.env, config={'seed': args.seed})

    # Initialize the agent and use random agents as opponents
    if args.algorithm == 'dqn':
        from rlcard.agents import DQNAgent
        agent = DQNAgent(num_actions=env.num_actions,
                         state_shape=env.state_shape[0],
                         mlp_layers=[128, 128],
                         device=device)
    elif args.algorithm == 'nfsp':
        from rlcard.agents import NFSPAgent
        agent = NFSPAgent(num_actions=env.num_actions,
                          state_shape=env.state_shape[0],
                          hidden_layers_sizes=[64, 64],
                          q_mlp_layers=[64, 64],
                          device=device)
    elif args.algorithm == 'dmc':
        from  rlcard.agents.dmc_agent import DMCTrainer
        agent = DMCTrainer(env,
                   load_model=args.load_model,
                   xpid=args.xpid,
                   savedir=args.savedir,
                   save_interval=args.save_interval,
                   num_actor_devices=args.num_actor_devices,
                   num_actors=args.num_actors,
                   training_device=args.training_device)
    agents = [agent]
    for _ in range(env.num_players):
        agents.append(RandomAgent(num_actions=env.num_actions))
    env.set_agents(agents)

    # Start training
    with Logger(args.log_dir) as logger:
        for episode in range(args.num_episodes):

            if args.algorithm == 'nfsp':
                agents[0].sample_episode_policy()

            # Generate data from the environment
            trajectories, payoffs = env.run(is_training=True)

            # Reorganaize the data to be state, action, reward, next_state, done
            trajectories = reorganize(trajectories, payoffs)

            # Feed transitions into agent memory, and train the agent
            # Here, we assume that DQN always plays the first position
            # and the other players play randomly (if any)
            for ts in trajectories[0]:
                agent.feed(ts)

            # Evaluate the performance. Play with random agents.
            if episode % args.evaluate_every == 0:
                logger.log_performance(env.timestep, tournament(env, args.num_games)[0])


    # Save model
    save_path = os.path.join(args.log_dir, 'model.pth')
    torch.save(agent, save_path)
    print('Model saved in', save_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("dqn crew")
    parser.add_argument('--env', type=str, default='crew')
    parser.add_argument('--algorithm', type=str, default='dqn', choices=['dqn', 'nfsp', 'dmc'])
    parser.add_argument('--cuda', type=str, default='')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--num_episodes', type=int, default=5000)
    parser.add_argument('--num_games', type=int, default=2000)
    parser.add_argument('--evaluate_every', type=int, default=100)
    parser.add_argument('--log_dir', type=str, default='experiments/crew')
    parser.add_argument('--load_model', action='store_true',
                        help='Load an existing model')
    parser.add_argument('--xpid', default='doudizhu',
                        help='Experiment id (default: doudizhu)')
    parser.add_argument('--savedir', default='experiments/dmc_result',
                        help='Root dir where experiment data will be saved')
    parser.add_argument('--save_interval', default=30, type=int,
                        help='Time interval (in minutes) at which to save the model')
    parser.add_argument('--num_actor_devices', default=1, type=int,
                        help='The number of devices used for simulation')
    parser.add_argument('--num_actors', default=5, type=int,
                        help='The number of actors for each simulation device')
    parser.add_argument('--training_device', default=0, type=int,
                        help='The index of the GPU used for training models')

    args = parser.parse_args()

    os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda
    train(args)