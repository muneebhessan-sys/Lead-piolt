# LeadPilot Workflow Audit

Date: 2026-09-16

## 1. Accounts do not connect

- **Files/endpoints:** `frontend/src/main.tsx` (`api`, `connectOAuth`, `Integrations`); `backend/app/main.py` (`/api/v1/admin/oauth/begin`, `/api/v1/admin/oauth/callback`, `integration_status`); `backend/app/services/oauth/service.py`; `backend/app/services/oauth/providers.py`.
- **Current state:** Real OAuth code, but incomplete/broken in operation. Provider client IDs/secrets are required environment configuration. The frontend only reads `detail`, while the API error handler returns `error`, so configuration failures become `Request failed`. Meta OAuth is persisted as `META`, while Instagram/Facebook cards query separate provider names and can remain `NOT_CONFIGURED`.
- **Fix plan:** Preserve the real OAuth flow, expose API error details, map Meta-backed account state to the relevant cards, and add contract coverage. Configure provider credentials and redirect URIs in deployment.
- **Test plan:** Test error rendering contract, OAuth begin with configured credentials, persisted account status, and Meta status mapping.

## 2. Selective messaging sends to the wrong audience

- **Files/endpoints:** `frontend/src/CampaignWorkspace.tsx`; `backend/app/main.py` (`/api/v1/campaigns`, `/prepare`, `/send-selected`); `backend/app/models.py` (`CampaignItem`).
- **Current state:** The selected-send endpoint filters campaign items correctly, but campaign creation accepts an empty selection and the workspace silently substitutes `backend-configured-account` when no sender is selected. The legacy campaign screen does not implement lead selection.
- **Fix plan:** Require a non-empty lead selection and an explicit sender, reject selected IDs outside the campaign, and keep idempotent per-lead delivery.
- **Test plan:** Verify only selected campaign items are sent, empty selections are rejected, and unselected IDs cannot be injected.

## 3. Voice recording/transcription is missing

- **Files/endpoints:** `backend/app/main.py` (`/api/v1/leads/{lead_id}/call`); `backend/app/services/voice/provider.py`; `backend/app/models.py` (`Call`).
- **Current state:** Stubbed completion behavior. Call start creates a synthetic text transcript and PDF immediately, then stores the PDF path as `recording_url`; no provider recording or completed transcript is fetched or persisted.
- **Fix plan:** Persist provider metadata returned at call start, accept an authenticated provider completion callback, and save only real `recording_url`, `transcript`, duration, and timestamps from callback payloads.
- **Test plan:** Confirm call start does not fabricate a transcript/recording and callback persistence stores supplied recording/transcript fields.

## 4. WhatsApp number verification does nothing

- **Files/endpoints:** `frontend/src/main.tsx` (`requestPhoneVerification`); `backend/app/main.py` (`/api/v1/admin/contact-profile/{phone_key}/verification-request`).
- **Current state:** Stub. The endpoint validates E.164 format and returns an informational message; it never creates or sends an OTP and never verifies one.
- **Fix plan:** Persist a short-lived hashed OTP challenge, add a confirmation endpoint, update the UI to accept the code, and mark the WhatsApp phone verified only after successful confirmation. Production must connect a real WhatsApp/SMS verification sender; development mode exposes the generated code only in the response for local testing.
- **Test plan:** Test challenge creation, invalid/expired code rejection, successful verification, and UI error handling.

## Effort estimate

- Code changes and focused tests: approximately 1-2 engineering days.
- External setup and live verification: approximately 0.5-2 days depending on Meta/Google/voice provider approval, credentials, callback URLs, and webhook configuration.
