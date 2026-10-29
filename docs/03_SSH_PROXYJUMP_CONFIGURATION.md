# 03. SSH ProxyJump Configuration & Secure Access Guide

## 1. Why SSH ProxyJump? (Security Architecture)

In traditional, naive architectures, administrators often copied their private SSH key (`.pem`) onto the Bastion host to connect from the Bastion into internal instances. **This is an enterprise anti-pattern and a major security vulnerability.**

If the Bastion host were compromised, an attacker would gain immediate access to the private key and compromise all internal database and application tiers.

### The Modern Solution: SSH ProxyJump (`-J`)
With SSH `ProxyJump`, your local laptop initiates an end-to-end encrypted SSH session directly with the private instance (`App-A` or `App-B`). The Bastion host acts strictly as an untrusted TCP forwarding proxy (`nc` / TCP pipe) on port 22:
* The private key **never leaves your local laptop**.
* The Bastion host cannot decrypt the payload or impersonate your credentials.

---

## 2. Configuration Setup

### Step 1: Store and Restrict Key Permissions
Place your `ewb-lab.pem` file in `~/.ssh/` and set proper read-only permissions:

#### On Linux / macOS / WSL:
```bash
mkdir -p ~/.ssh
mv /path/to/downloaded/ewb-lab.pem ~/.ssh/ewb-lab.pem
chmod 400 ~/.ssh/ewb-lab.pem
```

#### On Windows (PowerShell):
If Windows complains about open permissions on `.pem`:
```powershell
icacls "$HOME\.ssh\ewb-lab.pem" /inheritance:r
icacls "$HOME\.ssh\ewb-lab.pem" /grant:r "$($env:USERNAME):(R)"
```

---

### Step 2: Configure `~/.ssh/config`
Edit or create your configuration file:
* **Windows path:** `C:\Users\<username>\.ssh\config`
* **Linux/Mac/WSL path:** `~/.ssh/config`

Add the following block (replace `BASTION_PUBLIC_IP` with your actual bastion public IPv4):

```ssh
Host ewb-bastion
    HostName BASTION_PUBLIC_IP
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion
```

---

## 3. Testing Connections

1. **Connect to Bastion Host:**
   ```bash
   ssh ewb-bastion
   ```
   Type `exit` to return to your local machine.

2. **Connect to App-A directly via Bastion:**
   ```bash
   ssh ewb-app-a
   ```
   Verify you are logged in to `10.10.2.10`. Type `exit` to return.

3. **Connect to App-B directly via Bastion & Peering:**
   ```bash
   ssh ewb-app-b
   ```
   Verify you are logged in to `10.20.1.10`.
