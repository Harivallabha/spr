# Data-Efficient Reinforcement Learning with Self-Predictive Representations

*Max Schwarzer\*, Ankesh Anand\*, Rishab Goel, R Devon Hjelm, Aaron Courville, Philip Bachman*

This repo provides code for implementing the [SPR paper](https://arxiv.org/abs/2007.05929)

* [📦 Install ](#install) -- Install relevant dependencies and the project
* [🔧 Usage ](#usage) -- Commands to run different experiments from the paper

## Install 
To install the requirements, follow these steps:
```bash
# PyTorch
conda install pytorch torchvision -c pytorch
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Install requirements
pip install -r requirements.txt

# Login to W&B
wandb login {wandb_key}

# Finally, install the project
pip install --user -e git+git://github.com/ankeshanand/abstract-world-models
```

## Usage:
The default branch for the latest and stable changes is `release`. 

* To run with augmentation
```bash
python -m scripts.run --game pong --momentum-tau 1.
```

* To run without augmentation
```bash
python -m scripts.run --game pong --augmentation none --target-augmentation 0 --dropout 0.5
```

## What does each file do? 

    .
    ├── scripts
    │   └── run.py                # The main runner script to launch jobs.
    ├── src                     
    │   ├── agent.py              # Implements the Agent API for action selection 
    │   ├── algos.py              # Distributional RL loss
    │   ├── models.py             # Network architecture and forward passes.
    │   ├── rlpyt_atari_env.py    # Slightly modified Atari env from rlpyt
    │   ├── rlpyt_utils.py        # Utility methods that we use to extend rlpyt's functionality
    │   └── utils.py              # Command line arguments and helper functions 
    │
    └── requirements.txt          # Dependencies
