# Authentication & Token Management -- BlueOptima

This document describes how to authenticate and manage tokens when
interacting with the BlueOptima API.

## Overview

To use any BlueOptima API, a caller must first authenticate with the
BlueOptima server to obtain a JSON Web Token (JWT).\
Authentication can be performed in two ways:

1.  **Username and Password**
2.  **Personal Access Token (PAT)**

The generated token must be sent in the header of every subsequent API
request.

------------------------------------------------------------------------

## 1. Authentication Using Username & Password

**Endpoint:**\
`POST /v1/authenticate`

### Request Body

``` json
{
  "userName": "example@email.com",
  "password": "xxxxxxxx"
}
```

### Response

``` json
{
  "token": "xxxxxxxxx",
  "isFirstLogin": false
}
```

### Important Response Fields

-   **token** -- JWT used for all API calls\
-   **isFirstLogin** -- indicates first time access\
-   **isOtherSession** -- another session is active\
-   **showCaptcha** -- captcha required due to failed attempts\
-   **userDisabled** -- account disabled

------------------------------------------------------------------------

## 2. Personal Access Tokens (PAT)

PATs are long‑lived credentials used instead of passwords.\
They provide:

-   Secure automated access\
-   Granular permissions\
-   Ability to revoke without changing password

### Generating PAT from UI

1.  Open **My Profile**
2.  Go to **Personal Access Token** tab
3.  Click **Create Token**
4.  Enter name and expiration
5.  Copy token -- it will not be shown again

> Only one active PAT can exist at a time.

------------------------------------------------------------------------

## 3. Authenticating with PAT

**Endpoint** `POST https://iam.blueoptima.com/api/v1/authenticate/pat`

### Example (cURL)

``` bash
curl --request POST https://iam.blueoptima.com/api/v1/authenticate/pat --header 'Content-Type: application/json' --data '{"personalAccessToken":"xxxx"}'
```

### Response

``` json
{
  "token": "...",
  "isFirstLogin": false
}
```

------------------------------------------------------------------------

## 4. Making API Calls

### Header Required

    X-Auth-Token: <TOKEN>
    Content-Type: application/json

### Example -- Get Profile

`GET https://uix.blueoptima.com/api/v4/profile`

------------------------------------------------------------------------

## 5. Token Expiry & Refresh

-   Tokens expire after **10 minutes**
-   Use refresh API when 401 is returned

**Endpoint** `GET https://uix.blueoptima.com/api/v1/refreshToken`

------------------------------------------------------------------------

## Workflow Summary

1.  Authenticate (Password or PAT)
2.  Receive JWT token
3.  Call APIs with token
4.  Refresh token when expired

------------------------------------------------------------------------

© BlueOptima 2006‑2026
