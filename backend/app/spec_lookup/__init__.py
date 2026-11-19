"""Reference-number look-up: fill watch specs from outside sources.

- WatchBase Data Feed API (needs the owner's own key) gives the watch.
- Caliber Corner caliber pages give movement facts (personal use, credited).
- Without a key, the look-up still answers with links to search by hand.

Nothing here raises to the caller: every problem becomes a status and a
plain message (see service.lookup).
"""
