"""Central in-memory store shared across all cogs."""
from typing import Any

# Verification
verification_channels: dict[int, int] = {}           # guild_id -> channel_id
pending_verifications: dict[int, dict[int, int]] = {} # guild_id -> {msg_id: member_id}

# Autoname
autoname_guilds: set[int] = set()

# Wipes  guild_id -> [{name, date_str, time_str, ip, dt, channel_id, msg_id, reminded_1h, reminded_10m}]
wipes: dict[int, list[dict]] = {}

# Reaction-role tag messages
tag_messages: set[int] = set()

# Squad assignments  guild_id -> {member_id -> squad_role_str}
squad_assignments: dict[int, dict[int, str]] = {}

# Raid log  guild_id -> [{target, grid, caller_id, ts}]
raid_log: dict[int, list[dict]] = {}

# Base locations  guild_id -> [{name, grid, added_by, ts}]
base_locations: dict[int, list[dict]] = {}

# Farm log  guild_id -> [{resource, amount, member_id, member_name, ts}]
farm_log: dict[int, list[dict]] = {}

# Warnings  guild_id -> {member_id -> [{reason, ts, by_name}]}
warnings: dict[int, dict[int, list[dict]]] = {}

# Mutes  guild_id -> {member_id -> {until_ts, task}}
muted_members: dict[int, dict[int, Any]] = {}

# Scrap economy  guild_id -> {member_id -> balance}
scrap_balances: dict[int, dict[int, int]] = {}

# Meetings  guild_id -> [{topic, time_str, msg_id, channel_id, confirmed, declined, status, created_by}]
meetings: dict[int, list[dict]] = {}

# Agenda  guild_id -> [{title, date, time, note, added_by}]
agenda_events: dict[int, list[dict]] = {}

# Live status  guild_id -> (channel_id, msg_id)
status_channels: dict[int, tuple[int, int]] = {}

# Events (evento)  guild_id -> [{name, prize, end_ts, msg_id, channel_id, done}]
active_events: dict[int, list[dict]] = {}
