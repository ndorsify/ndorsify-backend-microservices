# 4. Reassign profile-service off browser-blocked port 6000

Date: 2026-08-28

## Status

Accepted

## Context

profile-service inherited port **6000** from the original Java service. During a
live browser smoke test of the SPA, every call to it failed with
`net::ERR_UNSAFE_PORT`: **Chromium (and Firefox) hard-block port 6000** — it is
the X11 port on their restricted-ports list. The service itself was healthy
(reachable via `curl`); browsers simply refuse to connect.

Because Phase 1 has no API gateway yet, the SPA calls each service directly by
origin, so a browser-blocked port makes profile-service unreachable from the
frontend.

## Decision

Move profile-service from **6000 → 6060** (a port outside the browsers'
restricted list and not colliding with the other services: users 1000,
dynamic-content 5000, messaging 3000, discovery 9000).

Updated: the service config default, `docker-compose.yml`, `Dockerfile`,
`.env.example`, and the docs. The frontend's `REACT_APP_PROFILE_URL` default
moves to `http://localhost:6060` in a paired change.

## Consequences

- The SPA can reach profile-service directly again.
- This is a point fix, not the general solution. The **API gateway** (a Phase 1
  foundation) remains the right long-term answer: it puts every service behind
  one safe origin, which also collapses the per-service CORS + base-URL story.
  When the gateway lands, the browser stops calling service ports directly and
  this constraint disappears.
- Other assigned ports were checked against the block list and are safe; only
  6000 needed to move. (Port 5000 is fine for browsers; note it collides with
  macOS AirPlay Receiver locally — a per-machine dev annoyance, not a code issue.)
