"""One-command local Docker bootstrap. Never prints secrets or overwrites an existing .env."""
import secrets,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=root/'.env'
if not env.exists():
    env.write_text((root/'.env.example').read_text().replace('POSTGRES_PASSWORD=\n','POSTGRES_PASSWORD='+secrets.token_urlsafe(32)+'\n'))
    env.chmod(0o600)
subprocess.run(['docker','compose','up','--build','-d'],cwd=root,check=True)
print('CareerLens AI: http://localhost:3000')
