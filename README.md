# ValtheraDB Conduit

ValtheraDB Conduit packages ValtheraDB as a compiled Bun binary for embedding from any parent process.

## Protocol

Conduit communicates over `stdin` and `stdout`. `stderr` is reserved for diagnostics and must not be parsed as protocol data.

Every frame starts with a 12 byte little-endian header:

```text
u32LE frameType
u32LE dbNameLength
u32LE payloadLength
dbNameLength bytes UTF-8 DB name
payloadLength bytes payload
```

Frame type decides the payload transfer format. The base protocol uses JSON payloads, but future releases can add other transfer formats by adding new frame types without changing the header.

### Base JSON Frames

| Direction | Type | Name | DB name | Payload |
| --- | ---: | --- | --- | --- |
| in | 1 | `INIT_DB` | required | `{ "dir": "./data", "opts": {} }` |
| in | 2 | `EXECUTE_JSON` | required | `{ "op": "find", "body": { "collection": "users" } }` |
| in | 3 | `CLOSE_DB` | required | `{}` |
| in | 4 | `LIST_DBS` | empty | `{}` |
| in | 5 | `PING` | empty | `{}` |
| in | 6 | `SHUTDOWN` | empty | `{}` |
| out | 100 | `READY` | empty | `{ "ok": true, "result": { "name": "ValtheraDB Conduit", "protocolVersion": 1, "coreVersion": "...", "dirVersion": "..." } }` |
| out | 101 | `RESULT_JSON` | copied | `{ "ok": true, "result": ... }` |
| out | 102 | `ERROR_JSON` | copied | `{ "ok": false, "code": "...", "message": "..." }` |
| out | 104 | `PONG` | empty | `{ "ok": true, "result": { "name": "ValtheraDB Conduit", "protocolVersion": 1, "coreVersion": "...", "dirVersion": "..." } }` |

## License

MIT
