# User Login & AWS Credentials

## Flow

1. **Register** (`POST /api/register`): Email + password. Email is the unique user ID.
2. **Login** (`POST /api/login`): Email + password. Sets a session cookie.
3. **Add credentials** (`POST /api/credentials`): Provide either:
   - `access_key` + `secret_key` (preferred)
   - `role_arn` only
4. **List buckets** (`GET /api/buckets`): Uses your stored credentials to list S3 buckets.
5. **Select bucket** (`POST /api/buckets/select`): Choose which bucket contains your CloudTrail logs.

## Credential storage

- **Access key + secret**: Encrypted at rest with Fernet (symmetric encryption).  
  Set `CREDENTIALS_ENCRYPTION_KEY` in `.env` for production.
- **IAM role ARN**: Stored as plain text (an ARN is not a secret).

## IAM Role ARN – assume role dynamically

You asked: "assume role dynamically is not preferred."

**Current behavior:**

- **Access keys**: Stored encrypted and used directly to call S3. No role assumption.
- **IAM role ARN**: If the user provides *only* a role ARN (no access keys), the backend must call `sts:AssumeRole()` to get temporary credentials before listing buckets or reading S3. That is the only way to use a role ARN for AWS API calls.

**Because assume role dynamically is not preferred:**

- Access key + secret is the primary, recommended path.
- If you want to avoid role assumption entirely, support only access keys:
  - Do not allow users to submit *only* a role ARN.
  - Treat role ARN as optional metadata (e.g. for display or future use).
- To fully drop AssumeRole support, the backend would need to:
  1. Reject `role_arn` when no access keys are provided, or
  2. Remove IAM role ARN as a credential option and use only access keys.

Right now, both options are implemented: access keys are preferred; role ARN is supported via AssumeRole when no keys are given.

## API summary

| Method | Endpoint            | Auth required | Description                    |
|--------|---------------------|---------------|--------------------------------|
| POST   | `/api/register`     | No            | Register with email + password |
| POST   | `/api/login`        | No            | Login, sets session            |
| POST   | `/api/logout`       | No            | Clear session                  |
| GET    | `/api/me`           | Yes           | Current user info              |
| POST   | `/api/credentials`  | Yes           | Add/update AWS credentials     |
| GET    | `/api/buckets`      | Yes           | List S3 buckets                |
| POST   | `/api/buckets/select` | Yes         | Set CloudTrail bucket          |

## Environment variables

- `SECRET_KEY`: Flask session secret. Required in production.
- `CREDENTIALS_ENCRYPTION_KEY`: Fernet key or passphrase for encrypting AWS secrets.
