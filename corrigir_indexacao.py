import boto3
import os
import re

BUCKET = "rekognition-service-face"
REGION = "us-east-2"
COLLECTION_ID = "2"
PREFIX = "2/"

s3 = boto3.client("s3", region_name=REGION)
rekognition = boto3.client("rekognition", region_name=REGION)

# ─── 1. Remove entradas com formato errado (as que nosso script criou) ────────
print("=== Passo 1: Removendo entradas com formato errado ===\n")

faces_erradas = []
next_token = None

while True:
    kwargs = {"CollectionId": COLLECTION_ID, "MaxResults": 4096}
    if next_token:
        kwargs["NextToken"] = next_token
    resp = rekognition.list_faces(**kwargs)

    for face in resp.get("Faces", []):
        eid = face.get("ExternalImageId", "")
        # Formato errado: começa com "2_" (nosso script adicionou o prefixo da pasta)
        if eid.startswith("2_"):
            faces_erradas.append(face["FaceId"])

    next_token = resp.get("NextToken")
    if not next_token:
        break

print(f"{len(faces_erradas)} entrada(s) com formato errado encontrada(s).")

if faces_erradas:
    # Rekognition aceita até 4096 por vez
    for i in range(0, len(faces_erradas), 4096):
        batch = faces_erradas[i:i+4096]
        rekognition.delete_faces(CollectionId=COLLECTION_ID, FaceIds=batch)
    print(f"Removidas {len(faces_erradas)} entrada(s).\n")
else:
    print("Nada a remover.\n")

# ─── 2. Renomeia arquivos WhatsApp no S3 e re-indexa ─────────────────────────
print("=== Passo 2: Renomeando e re-indexando arquivos WhatsApp ===\n")

paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=BUCKET, Prefix=PREFIX)

whatsapp_files = []
for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        nome = os.path.basename(key)
        if "WhatsApp" in nome or " " in nome or "(" in nome:
            whatsapp_files.append(key)

print(f"{len(whatsapp_files)} arquivo(s) WhatsApp encontrado(s).\n")

for old_key in whatsapp_files:
    nome = os.path.basename(old_key)
    # Gera nome limpo: remove espaços, parênteses e caracteres especiais
    nome_limpo = re.sub(r"[^a-zA-Z0-9._-]", "_", nome)
    nome_limpo = re.sub(r"_+", "_", nome_limpo).strip("_")
    new_key = PREFIX + nome_limpo

    print(f"Renomeando:")
    print(f"  {old_key}")
    print(f"  -> {new_key}")

    try:
        # Copia para novo nome
        s3.copy_object(
            Bucket=BUCKET,
            CopySource={"Bucket": BUCKET, "Key": old_key},
            Key=new_key,
        )
        # Remove arquivo antigo
        s3.delete_object(Bucket=BUCKET, Key=old_key)

        # Indexa com formato correto: nome sem extensão
        external_id = os.path.splitext(nome_limpo)[0]
        resp = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={"S3Object": {"Bucket": BUCKET, "Name": new_key}},
            ExternalImageId=external_id,
            DetectionAttributes=[],
            MaxFaces=1,
            QualityFilter="AUTO",
        )
        n = len(resp.get("FaceRecords", []))
        if n > 0:
            print(f"  OK — {n} rosto(s) indexado(s) com ExternalImageId='{external_id}'\n")
        else:
            unindexed = resp.get("UnindexedFaces", [])
            reasons = [u["Reasons"] for u in unindexed] if unindexed else []
            print(f"  -- nenhum rosto detectado. Motivo: {reasons}\n")

    except Exception as e:
        print(f"  ERRO: {e}\n")

print("=== Pronto! ===")
