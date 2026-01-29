#!/bin/bash

# Define environment name
VENV_NAME="venv"

echo "🚀 Setting up the environment..."

# Check if python3 is available
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 could not be found. Please install Python."
    exit 1
fi

# Create virtual environment
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating virtual environment '$VENV_NAME'..."
    python3 -m venv $VENV_NAME
else
    echo "Reusing existing virtual environment '$VENV_NAME'."
fi

# Activate virtual environment
source $VENV_NAME/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found!"
fi

echo "✅ Setup complete!"
echo ""
echo "To run the application, execute:"
echo "source $VENV_NAME/bin/activate"
echo "streamlit run app.py"
