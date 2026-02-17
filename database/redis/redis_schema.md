# Redis Key Structure Documentation

## Database Assignment

| Redis DB | Service | Purpose |
|----------|---------|---------|
| DB 0 | Auth Service | Sessions, tokens, rate limiting |
| DB 1 | Plant Service | Plant data cache, search cache |
| DB 2 | Chatbot Service | Conversation context, RAG cache, rate limiting |
| DB 3 | User Service | User preferences, favorites cache |
| DB 4 | Search Service | Search results cache, autocomplete |

---

## DB 0 - Auth Service

### Session Management
```
sessions:user:{user_id}          HASH    Full session data (TTL: 24h)
    - session_id: string
    - email: string
    - roles: json_string
    - created_at: timestamp
    - last_activity: timestamp

sessions:token:{session_token}   STRING  Maps token -> user_id (TTL: 24h)
sessions:active:{user_id}        SET     Set of active session tokens
```

### Rate Limiting
```
ratelimit:login:{ip_address}     SORTED_SET  Sliding window rate limit (TTL: 60s)
ratelimit:register:{ip_address}  SORTED_SET  Registration rate limit (TTL: 300s)
```

### Token Blacklist
```
blacklist:token:{jti}            STRING  Blacklisted JWT (TTL: matches token expiry)
```

---

## DB 1 - Plant Service

### Plant Data Cache
```
cache:plant:{plant_id}           STRING  JSON-serialized plant data (TTL: 1h)
cache:plant:list:{page}:{size}   STRING  Paginated plant list (TTL: 5m)
cache:compound:{compound_id}     STRING  JSON-serialized compound data (TTL: 1h)
```

### Search Cache
```
cache:search:{query_hash}        STRING  Cached search results (TTL: 5m)
```

### Counters (async update to DB)
```
counter:plant:views:{plant_id}   STRING  View count buffer (flushed periodically)
```

---

## DB 2 - Chatbot Service

### Conversation Context
```
conv:user:{user_id}:active       SORTED_SET  Active conversations sorted by last activity
conv:{conversation_id}:context   HASH        Current conversation context
    - intent: string
    - entities: json_string
    - turn_count: int
    - last_plant_id: string
conv:{conversation_id}:history   LIST        Recent message IDs (max 50)
```

### RAG Cache
```
cache:rag:{query_hash}           STRING  Cached RAG retrieval results (TTL: 30m)
```

### Rate Limiting
```
ratelimit:chatbot:{user_id}      STRING  Chatbot rate limit counter (TTL: 60s)
```

### User Presence
```
presence:user:{user_id}          STRING  "online" (TTL: 5m, refreshed on activity)
presence:online_count             STRING  Total online users
```

---

## DB 3 - User Service

### User Preferences Cache
```
cache:user:profile:{user_id}     STRING  JSON user profile (TTL: 15m)
cache:user:favorites:{user_id}   STRING  JSON favorites list (TTL: 5m)
```

### Recently Viewed
```
user:recent:{user_id}            LIST   Recently viewed plant IDs (max 50)
```

---

## DB 4 - Search Service

### Search Results Cache
```
cache:search:results:{query_hash}     STRING  Full search results (TTL: 5m)
cache:search:facets:{query_hash}      STRING  Facet/filter counts (TTL: 10m)
```

### Autocomplete
```
autocomplete:plants              SORTED_SET  Plant names for autocomplete
autocomplete:compounds           SORTED_SET  Compound names for autocomplete
```

### Popular Searches
```
popular:searches:daily           SORTED_SET  Daily search term frequency
popular:searches:weekly          SORTED_SET  Weekly search term frequency
```

---

## Key Naming Conventions

- Use colons `:` as separators
- Use lowercase for all key names
- Include the entity type after the namespace
- Include the ID as the last segment
- Always set TTL on cache keys
- Use `cache:` prefix for cacheable data
- Use `ratelimit:` prefix for rate limiting keys
