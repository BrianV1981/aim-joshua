#!/bin/bash

# A.I.M. Joshua OS Cloning System
# Quickly spin up fresh, isolated instances of the Joshua OS.

if [ -z "$1" ]; then
    echo "Usage: ./clone_joshua.sh <new_os_directory>"
    echo "Example: ./clone_joshua.sh aim-opencode-marketing"
    exit 1
fi

TARGET_DIR=$1
SOURCE_DIR="/home/kingb/aim-opencode"

if [ -d "$TARGET_DIR" ]; then
    echo "[ERROR] Target directory $TARGET_DIR already exists."
    exit 1
fi

echo "[1/4] Cloning Joshua blueprint to $TARGET_DIR..."
cp -r $SOURCE_DIR $TARGET_DIR

echo "[2/4] Scrubbing previous brain state, history, and artifacts..."
cd $TARGET_DIR

# Strip git history to make it a sovereign project
rm -rf .git

# Vaporize the old brain
rm -rf memory_lance/*
rm -rf archive/*
rm -rf workspace/*

# Remove old configurations so aim_init.py can generate fresh ones
rm -f .aim_core/CONFIG.json
rm -f core/CONFIG.json
rm -f aim-agy_os/.aim_core/CONFIG.json

echo "[3/4] Initializing fresh Git repository..."
git init
git add .
git commit -m "Initial commit: Joshua OS cloned from blueprint"

echo "[4/4] OS cloned successfully."
echo "--------------------------------------------------------"
echo "Your new Joshua instance is ready."
echo "Next Steps:"
echo "1. cd $TARGET_DIR"
echo "2. python3 aim-agy_os/.aim_core/aim_init.py"
echo "--------------------------------------------------------"
