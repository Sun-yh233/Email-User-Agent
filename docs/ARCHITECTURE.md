# Email User Agent - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Interface Layer                          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                        gui.py (944 lines)                       │  │
│  │                                                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │  │
│  │  │  Send Email     │  │  Receive Email  │  │   Settings    │  │  │
│  │  │  Interface      │  │  Interface      │  │   Windows     │  │  │
│  │  └─────────────────┘  └─────────────────┘  └───────────────┘  │  │
│  │          │                     │                     │          │  │
│  └──────────┼─────────────────────┼─────────────────────┼──────────┘  │
│             │                     │                     │             │
└─────────────┼─────────────────────┼─────────────────────┼─────────────┘
              │                     │                     │
              ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Business Logic Layer                           │
│                                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                   │
│  │   SMTP Client        │  │   POP3 Client        │                   │
│  │  smtp_client.py      │  │  pop3_client.py      │                   │
│  │    (213 lines)       │  │    (311 lines)       │                   │
│  │                      │  │                      │                   │
│  │  • Connect           │  │  • Connect           │                   │
│  │  • Authenticate      │  │  • Authenticate      │                   │
│  │  • Send Email        │  │  • List Emails       │                   │
│  │  • SSL/TLS Support   │  │  • Parse MIME        │                   │
│  │  • Encoder Interface │  │  • Decoder Interface │                   │
│  └──────────┬───────────┘  └──────────┬───────────┘                   │
│             │                         │                               │
│             └─────────────┬───────────┘                               │
│                           │                                           │
│  ┌────────────────────────┼────────────────────────┐                  │
│  │         Email Encoder  │  Config Manager        │                  │
│  │       email_encoder.py │  config_manager.py     │                  │
│  │         (321 lines)    │    (280 lines)         │                  │
│  │                        │                        │                  │
│  │  • Base64 Encoding     │  • Account Management  │                  │
│  │  • Custom Tables       │  • Settings Storage    │                  │
│  │  • Negotiation         │  • Provider Detection  │                  │
│  │  • One-time-pad        │  • JSON Persistence    │                  │
│  └────────────────────────┴────────────────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Protocol Layer                                │
│                                                                         │
│  ┌──────────────────────────┐  ┌──────────────────────────┐           │
│  │    SMTP Protocol         │  │    POP3 Protocol         │           │
│  │    (RFC 5321)            │  │    (RFC 1939)            │           │
│  │                          │  │                          │           │
│  │  • EHLO/HELO            │  │  • USER/PASS             │           │
│  │  • AUTH LOGIN           │  │  • STAT                  │           │
│  │  • MAIL FROM/RCPT TO    │  │  • RETR                  │           │
│  │  • DATA                 │  │  • DELE                  │           │
│  │  • SSL/TLS              │  │  • SSL                   │           │
│  └──────────┬───────────────┘  └──────────┬───────────────┘           │
│             │                             │                           │
└─────────────┼─────────────────────────────┼───────────────────────────┘
              │                             │
              ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Email Servers                                  │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   QQ     │  │   163    │  │  Sina    │  │  Gmail   │  ...         │
│  │  Mail    │  │   Mail   │  │   Mail   │  │          │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


Data Flow:

Send Email:
  User Input → GUI → SMTP Client → (Optional: Encoder) → SMTP Protocol → Server

Receive Email:
  Server → POP3 Protocol → POP3 Client → (Optional: Decoder) → Parse → GUI

Configure:
  User Input → GUI → Config Manager → JSON File

Secure Communication:
  User A (Encoder + Key) → Email Server → User B (Decoder + Same Key)


Module Dependencies:

main.py (38 lines)
  └── gui.py (944 lines)
       ├── smtp_client.py (213 lines)
       │    └── email_encoder.py (321 lines)
       ├── pop3_client.py (311 lines)
       │    └── email_encoder.py (321 lines)
       └── config_manager.py (280 lines)


Key Features:

1. Modular Architecture
   - Clean separation of concerns
   - High cohesion, low coupling
   - Easy to extend and maintain

2. Interface Design
   - Encoder/Decoder function interfaces
   - Provider-agnostic configuration
   - Pluggable components

3. Security
   - SSL/TLS support
   - Custom encoding interface
   - Shared secret negotiation

4. User Experience
   - Intuitive GUI
   - Multi-threaded operations
   - Comprehensive error handling

5. Cross-platform
   - Pure Python implementation
   - Standard library only
   - Works on Windows and Linux
```
