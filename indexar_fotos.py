import boto3

BUCKET = "rekognition-service-face"
REGION = "us-east-2"
COLLECTION_ID = "2"
PREFIX = "2/"

s3 = boto3.client("s3", region_name=REGION)
rekognition = boto3.client("rekognition", region_name=REGION)

# Garante que a collection existe
try:
    rekognition.create_collection(CollectionId=COLLECTION_ID)
    print(f"Collection '{COLLECTION_ID}' criada.")
except rekognition.exceptions.ResourceAlreadyExistsException:
    print(f"Collection '{COLLECTION_ID}' ja existe.")

# Lista todas as fotos na pasta 2/
paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=BUCKET, Prefix=PREFIX)

fotos = []
for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if key.lower().endswith((".jpg", ".jpeg", ".png")):
            fotos.append(key)

print(f"\n{len(fotos)} foto(s) encontrada(s) na pasta '{PREFIX}':\n")
for f in fotos:
    print(f"  {f}")

print()

# Indexa cada foto
for key in fotos:
    external_id = key.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    try:
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={"S3Object": {"Bucket": BUCKET, "Name": key}},
            ExternalImageId=external_id,
            DetectionAttributes=[],
            MaxFaces=1,
            QualityFilter="AUTO",
        )
        n = len(response.get("FaceRecords", []))
        unindexed = len(response.get("UnindexedFaces", []))
        if n > 0:
            print(f"OK  {key}")
            print(f"    {n} rosto(s) indexado(s)")
        else:
            print(f"--  {key}")
            print(f"    nenhum rosto detectado")
            if unindexed:
                reasons = [u["Reasons"] for u in response["UnindexedFaces"]]
                print(f"    motivo: {reasons}")
    except Exception as e:
        print(f"ERR {key}")
        print(f"    {e}")

print("\nPronto!")
