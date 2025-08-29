#/bin/zsh

# Creates a 'companion' mircomamba environment with ome-types

source  ~/.zshrc

# Check if micromamba is available
if ! command -v micromamba &> /dev/null; then
    echo "Error: micromamba is not installed or not in PATH"
    echo "Please install micromamba first: https://mamba.readthedocs.io/en/latest/installation.html"
    exit 1
fi


# Check if 'companion' environment already exists
if micromamba env list | grep -q "companion"; then
    echo "Environment 'companion' already exists."
else
    echo "Creating 'companion' environment..."
    micromamba create -n companion -c conda-forge python=3.12 -y
fi

micromamba activate companion
pip install -U ome-types
echo "Environment 'companion' has been set up."
echo "Enable it by running: micromamba activate companion"
