from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import os, ipaddress

CERT_DIR = "redis-tls"
os.makedirs(CERT_DIR, exist_ok=True)


def write_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


# ------------------------
# 1. Generate CA
# ------------------------

ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Redis Test CA")])

ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_name)
    .issuer_name(ca_name)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

write_file(
    f"{CERT_DIR}/ca.key",
    ca_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ),
)

write_file(
    f"{CERT_DIR}/ca.crt",
    ca_cert.public_bytes(serialization.Encoding.PEM),
)


# ------------------------
# 2. Generate server cert
# ------------------------

server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

server_name = x509.Name(
    [
        x509.NameAttribute(NameOID.COMMON_NAME, "redis"),
    ]
)

alt_names = x509.SubjectAlternativeName(
    [
        x509.DNSName("redis"),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
)

csr = (
    x509.CertificateSigningRequestBuilder()
    .subject_name(server_name)
    .add_extension(alt_names, critical=False)
    .sign(server_key, hashes.SHA256())
)


server_cert = (
    x509.CertificateBuilder()
    .subject_name(csr.subject)
    .issuer_name(ca_cert.subject)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(alt_names, critical=False)
    .sign(ca_key, hashes.SHA256())
)

write_file(
    f"{CERT_DIR}/server.key",
    server_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ),
)

write_file(
    f"{CERT_DIR}/server.crt",
    server_cert.public_bytes(serialization.Encoding.PEM),
)

print("✅ Redis TLS certificates generated in ./redis-tls/")
print("    - ca.crt")
print("    - ca.key")
print("    - server.crt")
print("    - server.key")
