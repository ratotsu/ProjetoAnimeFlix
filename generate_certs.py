"""
Gera certificados SSL auto-assinados para desenvolvimento.
Em produção, use Let's Encrypt ou outro certificado válido.
"""

import os
from pathlib import Path

def generate_self_signed_cert():
    """Gera certificado auto-assinado usando OpenSSL."""
    certs_dir = Path("certs")
    certs_dir.mkdir(exist_ok=True)
    
    cert_file = certs_dir / "cert.pem"
    key_file = certs_dir / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print("[SSL] Certificados já existem.")
        return
    
    print("[SSL] Gerando certificados SSL...")
    
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime
    
    # Gerar chave privada
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Configurar certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "StreamFlix"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(__import__('ipaddress').ip_address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(key, hashes.SHA256())
    
    # Salvar chave privada
    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Salvar certificado
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"[SSL] Certificados gerados em {certs_dir}/")
    print(f"  - Certificado: {cert_file}")
    print(f"  - Chave privada: {key_file}")

if __name__ == "__main__":
    try:
        generate_self_signed_cert()
    except ImportError:
        print("[SSL] Usando OpenSSL via linha de comando...")
        os.makedirs("certs", exist_ok=True)
        os.system('openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"')