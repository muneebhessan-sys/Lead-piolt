# LeadPilot Master Requirement Matrix

| Requirement | Status | Database | Backend/API | Frontend | Integration | Persistence | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| Lightweight local architecture | COMPLETE | SQLite | FastAPI | React/Vite | None required | Yes | PASS | No Docker/PostgreSQL/Redis/Celery/LLM runtime required. |
| Admin settings | PARTIAL | Service/voice/instruction records | Partial APIs | Partial admin UI | N/A | Yes | Partial | General settings and full editor are missing. |
| Service profile | PARTIAL | Yes | GET/PUT | Missing editor | N/A | Yes | API tested | Intelligence consumes it. |
| Custom instructions | PARTIAL | Yes | CRUD | Create/activate/delete | N/A | Yes | API tested | Edit/duplicate/preview/test UI missing. |
| Google Places | PARTIAL | Businesses/leads | Official Text Search provider | Status/test only | REQUIRES_USER_CONFIGURATION | Yes | Config state tested | Requires `GOOGLE_PLACES_API_KEY`; discovery UI missing. |
| Website audit/SSRF | PARTIAL | Audit record | Audit endpoint/persistence | Missing audit UI | HTTP | Yes | Private-IP blocking tested | Advanced link/accessibility checks incomplete. |
| Deterministic intelligence | PARTIAL | Uses stored records | Personalize API | Missing lead UI | Local Python | Yes | Pipeline tested | Classification/follow-up sophistication incomplete. |
| CRM/customers/projects | MISSING | Partial lead only | Partial lead list | Missing | N/A | Partial | Partial | Customer/project/timeline modules absent. |
| Messaging | PARTIAL | Messages | Draft/approve | Missing workflow UI | No sender | Yes | Draft/approve tested | Delivery/providers/campaigns absent. |
| Gmail OAuth | REQUIRES_USER_CONFIGURATION | No accounts/tokens | MISSING | Truthful unavailable state | Official OAuth required | No | Not run | Adapter not implemented. |
| Meta integrations | REQUIRES_USER_CONFIGURATION | No accounts/tokens | MISSING | Truthful unavailable state | Official Meta required | No | Not run | Adapter not implemented. |
| Campaigns | MISSING | No campaign tables | MISSING | MISSING | N/A | No | Not run | Required future work. |
| Local jobs | PARTIAL | Yes | State transitions | Jobs UI | Local | Yes | Enqueue/cancel tested | Execution/recovery/concurrency handlers incomplete. |
| Voice Agent | PARTIAL | Yes | Save/test health | Save/test UI | User endpoint required | Yes | Config state tested | Call contract cannot be invented. |
| Payments | REQUIRES_USER_CONFIGURATION | MISSING | MISSING | Truthful unavailable state | Provider required | No | Not run | No provider selected. |
| Logs/audit trail | MISSING | MISSING | Request ID only | Informational card | N/A | No | Not run | Safe persistent audit log missing. |
| Dashboard metrics | PARTIAL | Leads/jobs | Health only | Partial | N/A | Yes | Health tested | Full database metrics missing. |
| Themes/accessibility | PARTIAL | N/A | N/A | Dark only | N/A | N/A | Build PASS | Light theme/full accessibility missing. |
| Security/provider states | PARTIAL | N/A | SSRF + safe config states | No secret display | External states truthful | N/A | PASS subset | Auth, rate limits, headers and OAuth state missing. |
