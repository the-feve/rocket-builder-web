@echo off
rem Copies new Rocket Builder print orders to C:\RocketOrders.
rem Set ROCKET_SYNC_TOKEN once:  setx ROCKET_SYNC_TOKEN "the-token"
rem Then schedule this file in Task Scheduler (see tools\README.md).
cd /d "%~dp0"
python sync_orders.py --dest "C:\RocketOrders" >> "C:\RocketOrders\sync.log" 2>&1
