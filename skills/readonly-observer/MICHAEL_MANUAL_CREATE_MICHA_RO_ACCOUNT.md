# MICHAEL — Manual: Create the `micha-ro` account (one-time, ~2 minutes)

This is the **only** manual, phone-friendly step needed to start building the
**File Investigator (Readonly Observer)** agent. Everything else is designed and
staged; Goose will do the infrastructure once this account exists.

## Why you (Michael) must do this step
The whole point of the agent is a hard, OS-enforced **read-only** guarantee: it
can look at your whole machine but literally cannot change anything. That
guarantee is enforced by a dedicated, low-privilege Windows account named
`micha-ro` that runs the read-only file browser process. **The password for that
account must never be stored anywhere in the AI system** — only you will ever
know it. So you set it yourself, once, and it never enters LibreChat, Goose, any
skill, any config, or any trace.

You keep using the machine as `micha` (your normal account). `micha-ro` is never
logged into interactively — it only exists to run the read-only browser process.

## What you need
- Your Windows admin login (you are `micha`, an admin).
- An open PowerShell **as Administrator** (right-click → Run as administrator).
  On your phone via Termius, connect to `michael-pc` and open a PowerShell
  session as admin.

## Step 1 — open an admin PowerShell
In the Start menu search, type `PowerShell`, right-click **Windows PowerShell**,
and choose **Run as administrator**. Accept the UAC prompt.

## Step 2 — create the account
Copy each of these two lines exactly, one at a time, and press Enter:

```powershell
$pass = Read-Host -AsSecureString "Type a new strong password for micha-ro (only you will know it)"
New-LocalUser -Name "micha-ro" -Password $pass -Description "Read-only file observer - never log in interactively" -AccountNeverExpires -PasswordNeverExpires
```

It will prompt you to type a password (and again to confirm). Choose something
long and random — you'll never need to type it again after this step. **Do not
write it in chat, a file, or anywhere in the AI system.**

> Note: `New-LocalUser` does not add the account to `Administrators` — good.
> The account stays a standard user, which is exactly what we want (no admin
> write power).

## Step 3 — verify the account exists
```powershell
Get-LocalUser -Name "micha-ro"
```
You should see a row for `micha-ro` with **Enabled : True**.

## Step 4 — tell me it's done
Reply here with: **"micha-ro account created"**. Do NOT paste the password.

Once you confirm, I'll dispatch Goose to:
1. Apply the read-only ACLs (read-allow on exposed roots, deny write, deny the
   sensitive vaults).
2. Stand up the read-only MCP endpoint running as `micha-ro` (loopback only).
3. Run an adversarial test proving 0 writes and 0 secret leaks are possible.

## If something goes wrong
- If `New-LocalUser` errors with "parameter set cannot be resolved", make sure
  you're in an **elevated** PowerShell (admin), and that the password prompt step
  ran (the command waits for you to type one).
- If you already created `micha-ro` before, Step 3 will still return it — just
  reply "already exists".
- If unsure, tell me the error text and I'll give you the corrected line.
