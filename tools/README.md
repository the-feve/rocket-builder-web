# Tools

## `sync_orders.py`: print orders to a folder on your PC

Copies each new order from the website into `C:\RocketOrders\<batch>\<order id>\`:
the STLs, `ORDER.txt` (customer, shipping address, a checklist of parts to print)
and `order.json`. Orders are grouped by the day they came in (batch `B20261014`).
If an order's status changes (you mark it printing or shipped on the Orders page),
its `ORDER.txt` is updated on the next run.

Needs Python 3 (no extra packages).

### One-time setup (Windows)

1. Make a long random token and set it on Fly (keep it out of chat and git):
   `fly secrets set ROCKETGEN_SYNC_TOKEN=<token> -a rocket-fevergeon`
2. Save the same token on this PC (PowerShell): `setx ROCKET_SYNC_TOKEN "<token>"`, then open a new window.
3. Try it: `python tools\sync_orders.py --dest "C:\RocketOrders"`
4. Run it automatically: Task Scheduler → *Create Basic Task* → name it "Rocket orders" →
   *Daily*, then in the task's Properties → Triggers → Edit, tick *Repeat task every 15 minutes*
   for *Indefinitely*. Action: *Start a program* → `tools\sync_orders.bat` (full path).
   It logs to `C:\RocketOrders\sync.log`.

The site sleeps when idle, so the first run after a quiet spell can take ~20 s or say it
couldn't connect; the next run picks the orders up.
