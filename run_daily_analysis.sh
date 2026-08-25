#!/bin/bash
cd ~/Documents/stock_analysis_system
source venv/bin/activate
python test_system.py > logs/daily_analysis.log 2>&1
