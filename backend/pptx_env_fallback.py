import os

def load_envfile(path='/etc/stratgen.env'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # setze nur, wenn noch nicht vorhanden
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        # silent fail – Fallback soll nie den Dienst blockieren
        pass
