# ADR-002: Login, Session und CSRF

Status: Accepted
Datum: 2026-10-19
Entschieden von: Projektteam

## Kontext

Die Rollen in UC-001 und UC-002 müssen serverseitig aus einer Anmeldung
stammen. V1 benötigt für fiktive E2E-Abläufe reproduzierbare Demo-Benutzer.

## Alternativen

- A: Fiktive Seed-Demo-Benutzer mit E-Mail-/Passwort-Login und Session-Cookie.
- B: Öffentliche Registrierung oder Single Sign-on.

## Entscheid

V1 verwendet Seed-Demo-Benutzer. Passwörter werden mit Argon2 geprüft,
Sessions über sichere `HttpOnly`, `Secure`, `SameSite`-Cookies geführt und
schreibende Requests mit CSRF geschützt. `CurrentActorPort` liegt in
Application; Session- und Passwortadapter liegen in Infrastructure.

Präzisiert am 26.10.2026 (Abgleich mit dem Code): Ein eigener
`CurrentActorPort` wurde nicht umgesetzt. Die Session ist ein mit
`SESSION_SECRET` signiertes Cookie; die Interfaces-Schicht liest daraus den
`Actor` und übergibt ihn jedem Use Case als Parameter. Der Passwortadapter liegt
in Infrastructure (`infrastructure/auth.py`). Wie ein Logout das Cookie
ungültig macht, regelt ADR-007.

## Konsequenzen

Die E2E-Tests erhalten stabile fiktive Rollen. Eine öffentliche Registrierung
bleibt eine spätere Erweiterung; Rollen und Abteilungen werden nie aus
Formularwerten übernommen.